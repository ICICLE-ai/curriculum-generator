import os
import re
import logging
import tempfile
from typing import Dict, Any, List, Optional, Sequence

from digitalagedu.core.config import LLMModels
from digitalagedu.core.llm.ai_setup import ask_code, image_url, llm_kwargs, log_llm
from digitalagedu.core.llm.generation_trace import now_iso
from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.presentation_prompts import (
    ConceptVisualSpec,
    LessonPlan,
    LessonSlide,
    LESSON_PLANNER_SYSTEM,
    build_lesson_plan_prompt,
    SLIDE_BUILDER_SYSTEM,
    build_lesson_slide_prompt,
    build_slide_review_messages,
    SlideReview,
    solution_excerpt,
    SUBPROCESS_TIMEOUT_SECONDS,
)
from digitalagedu.core.llm.slide_deck_repl import (
    SafeTelemetryDict,
    SlideDeckRepl,
    execute_presentation_code_sandbox,
)
from digitalagedu.core.llm.slide_render import render_deck_pngs
from digitalagedu.core.llm.slide_kit.theme import layout_issues

logger = logging.getLogger(__name__)

# Re-exports for backward compatibility
__all__ = [
    "PresentationDesigner",
    "ConceptVisualSpec",
    "LessonPlan",
    "LessonSlide",
    "SlideDeckRepl",
    "SafeTelemetryDict",
    "execute_presentation_code_sandbox",
    "SUBPROCESS_TIMEOUT_SECONDS",
]


MAX_SLIDE_EXEC_FAILURES = 3  # code that crashes, fabricates data, or adds no slide
MAX_SLIDE_REVIEW_ROUNDS = 2  # screenshot reviews that may send a slide back; the last revision is kept unreviewed

_FAKE_DATA_CALL = re.compile(r"\bnp\.random\.|\brandom\.(choice|choices|rand|randint|random|normal|uniform|sample|shuffle)\(")
_FAKE_DATA_COMMENT = re.compile(r"#.*\b(simulat\w*|dummy|synthetic|fake|placeholder data|sample data|for demonstration)", re.IGNORECASE)


def synthetic_data_issue(code: str) -> Optional[str]:
    """Why slide code fabricates data instead of plotting this run's real values, or None.
    shortcut: pattern check on random calls and 'simulated/dummy/sample data' comments; a model that fakes data
    silently (hardcoded lists, no comment) still passes. Upgrade to checking plotted labels against the dataset's classes."""
    call = _FAKE_DATA_CALL.search(code or "")
    comment = _FAKE_DATA_COMMENT.search(code or "")
    if call or comment:
        found = (call or comment).group(0).strip()
        return (f"Rejected before running: the code fabricates data ({found!r}). Plot only real values from "
                f"`telemetry`, `artifacts` or `pd.read_csv(artifacts['results_csv'])`, using this dataset's class names.")
    return None


class PresentationDesigner:
    """
    Two-Stage Autonomous Presentation Designer:
    1. Lesson planner: orders the week as goal -> overview -> method (each in depth) -> why -> application slides.
    2. Sequential Slide Builder Loop: generates, runs and reviews one slide per planned slide in a stateful
       REPL, with the deck outline as context so slides build on each other.
    """

    def __init__(self, client: Any = None, model_name: Optional[str] = None, code_client: Any = None,
                 reviewer_model: Optional[str] = None, plan_model: Optional[str] = None):
        self.client = client  # instructor client: structured lesson plan and slide reviews
        self.code_client = code_client  # plain OpenAI client: slide code as fenced python blocks
        self.model_name = model_name or LLMModels().slides
        self.reviewer_model = reviewer_model or LLMModels().slide_reviewer  # must accept images
        self.plan_model = plan_model or LLMModels().planner

    def _get_matching_recipe(self, title: str, visual_idea: str) -> str:
        """Retrieves matching atomic visual recipe from Qdrant or local fallback."""
        query = f"{title} {visual_idea}".strip()
        try:
            from digitalagedu.core.llm.context import _get_qdrant_client
            qdrant = _get_qdrant_client()
            if qdrant and getattr(qdrant, "is_available", True):
                matches = qdrant.query_similar(
                    query_text=query,
                    chunk_type="presentation_recipe",
                    top_k=1
                )
                if matches and matches[0].get("text"):
                    return matches[0]["text"]
        except Exception as e:
            logger.debug(f"Qdrant recipe lookup skipped: {e}")

        # Local match from VISUAL_RECIPES
        try:
            from digitalagedu.core.llm.visuals.visual_recipes import VISUAL_RECIPES
            query_lower = query.lower()
            for r in VISUAL_RECIPES:
                if any(t in query_lower for t in r["topics"]):
                    return r["text"]
            return ""
        except Exception:
            return ""

    def _plan_lesson(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        solution_code: str,
        telemetry: Dict[str, Any],
        artifacts: Optional[Dict[str, str]] = None
    ) -> Optional[LessonPlan]:
        """The planner model orders the week's deck as goal -> overview -> method -> why -> application slides;
        LessonPlan's validators re-ask until the flow, method depth and code placement hold."""
        if not self.client:
            return None
        prompt = build_lesson_plan_prompt(module, problem_formulation, solution_code, telemetry, artifacts)
        try:
            plan = self.client.chat.completions.create(
                model=self.plan_model,
                response_model=LessonPlan,
                max_retries=3,  # re-asked when the flow or a slide's text budget is off
                max_tokens=32768,
                messages=[{"role": "system", "content": LESSON_PLANNER_SYSTEM}, {"role": "user", "content": prompt}],
                **llm_kwargs(self.plan_model),
            )
            log_llm(f"Lesson plan '{plan.deck_title}': {len(plan.slides)} slides, methods {plan.methods}")
            return plan
        except Exception as e:
            logger.warning(f"Lesson planning LLM call encountered error: {e}.")
        return None

    def _build_slide(self, repl: SlideDeckRepl, system: str, prompt: str, label: str,
                     trace=None, artifact: str = "slide_code", used=(),
                     required_text: Sequence[str] = (), speaker_notes: str = "", review_focus: str = "") -> None:
        """Asks the LLM for one slide's code and runs it: an execution failure is retried with the error (up to
        MAX_SLIDE_EXEC_FAILURES), and a slide that runs is rendered and shown to the vision reviewer, whose fixes
        are sent back for revision (up to MAX_SLIDE_REVIEW_ROUNDS). Raises if no slide was added.
        Code that fabricates data is rejected unrun; a slide missing any `required_text` is removed and retried.
        With a GenerationTrace, each code version, REPL execution and review is recorded as PROV activities."""
        slides_before = len(repl.prs.slides)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        exec_activity, purpose = None, "generate"
        failures = reviews = 0
        try:
            while failures < MAX_SLIDE_EXEC_FAILURES:
                code = ask_code(
                    self.code_client, self.model_name, messages, f"{label} slide code", max_tokens=16384,
                    trace=trace, agent="slide_builder", artifact=artifact,
                    purpose=purpose, used=used, informed_by=exec_activity,
                )
                start = now_iso()
                fabricated = synthetic_data_issue(code)
                success, output_msg = (False, fabricated) if fabricated else repl.execute_snippet(code)
                slide_added = len(repl.prs.slides) > slides_before
                if success and slide_added:
                    slide_text = " ".join(
                        sh.text_frame.text for s in list(repl.prs.slides)[slides_before:] for sh in s.shapes if sh.has_text_frame
                    )
                    missing = [t for t in required_text if t and t not in slide_text]
                    if missing:
                        repl._drop_slides_from(slides_before)
                        success, slide_added = False, False
                        output_msg = f"The slide is missing required content: {missing}."
                if trace is not None:
                    exec_activity = trace.add_activity(
                        "slide_exec", "slide_repl", start=start, label=label, success=success,
                        slide_added=slide_added, error=None if success else str(output_msg)[-2000:],
                    )
                    trace.relate("used", activity=exec_activity, entity=trace.latest[artifact])
                # ask_code already appended this attempt's reply to messages
                if success and slide_added:
                    issues = self._review_slide(repl, label, review_focus, trace) if reviews < MAX_SLIDE_REVIEW_ROUNDS else []
                    if not issues:
                        if speaker_notes:
                            repl.prs.slides[-1].notes_slide.notes_text_frame.text = speaker_notes
                        return
                    reviews += 1
                    repl._drop_slides_from(slides_before)
                    purpose = "slide_review_revision"
                    messages.append({"role": "user", "content": (
                        "A reviewer looked at a screenshot of your slide and asks for these fixes:\n"
                        + "\n".join(f"- {i}" for i in issues)
                        + "\nReturn the complete revised code that adds exactly one slide.")})
                    continue
                failures += 1
                purpose = "slide_exec_retry"
                if failures < MAX_SLIDE_EXEC_FAILURES:
                    logger.warning(f"{label} attempt failed ({output_msg}). Retrying with self-healing feedback...")
                    messages.append({"role": "user", "content": f"Execution issue:\n{output_msg}\nEnsure a graphic is rendered and slide_kit adds exactly one slide to `prs` for {label}. Return corrected Python code."})
        except Exception as call_err:
            logger.warning(f"LLM slide generation error on {label}: {call_err}")
        raise RuntimeError(f"Failed to generate {label} slide after {MAX_SLIDE_EXEC_FAILURES} failed attempts.")

    def _review_slide(self, repl: SlideDeckRepl, label: str, focus: str, trace=None) -> List[str]:
        """Fixes for the deck's last slide: overlapping or off-slide elements from shape geometry (always), plus
        the vision reviewer's verdict on a rendered screenshot shown next to the earlier slides for variety.
        The vision part is skipped without a client or renderer, or on a reviewer error: a review must never
        cost the slide. Returns [] when the slide is accepted."""
        start = now_iso()
        issues = layout_issues(repl.prs.slides[-1])
        deck = os.path.join(repl.temp_dir, "review_deck.pptx")
        pngs = []
        if self.client is not None:
            repl.prs.save(deck)
            pngs = render_deck_pngs(deck, repl.temp_dir)
        if pngs:
            try:
                review = self.client.chat.completions.create(
                    model=self.reviewer_model, response_model=SlideReview, max_retries=2, max_tokens=8192,
                    messages=build_slide_review_messages(label, focus, image_url(pngs[-1]), [image_url(p) for p in pngs[:-1][-3:]]),
                    **llm_kwargs(self.reviewer_model),
                )
                if not review.acceptable:
                    issues += [i for i in review.issues if i.strip()] or ["Improve the slide's readability."]
            except Exception as err:
                logger.warning(f"Slide review failed for {label}, keeping the slide: {err}")
        log_llm(f"{label} review ({'screenshot + geometry' if pngs else 'geometry only'}): "
                + ("accepted" if not issues else f"{len(issues)} fixes: " + " | ".join(issues))[:600])
        if trace is not None:
            trace.add_activity("slide_review", "slide_reviewer", start=start, label=label, model=self.reviewer_model,
                               acceptable=not issues, issues=issues)
        return issues

    def generate_presentation_deck(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        solution_code: str,
        telemetry: Dict[str, Any],
        output_path: str,
        artifacts: Optional[Dict[str, str]] = None,
        trace=None
    ) -> Optional[str]:
        """
        Plans the week as a lesson (goal -> overview -> method -> why -> application), then builds a title slide,
        one REPL-built and reviewed slide per planned slide, and a closing takeaways slide.
        """
        if not self.client:
            logger.info("No LLM client provided to PresentationDesigner. Skipping presentation generation.")
            return None

        logger.info(f"Planning the lesson deck for module '{module.title}'...")
        plan = self._plan_lesson(
            module=module,
            problem_formulation=problem_formulation,
            solution_code=solution_code,
            telemetry=telemetry,
            artifacts=artifacts
        )
        if not plan:
            raise RuntimeError(f"Lesson planning failed to generate a plan for '{module.title}'.")
        plan_entity = None
        if trace is not None:
            plan_entity = trace.add_entity("lesson_plan", plan.model_dump_json(indent=2), ext="json")
            trace.relate("wasAttributedTo", entity=plan_entity, agent=trace.agent("lesson_planner"))
            if trace.latest.get("solution"):
                trace.relate("wasDerivedFrom", generatedEntity=plan_entity, usedEntity=trace.latest["solution"])

        with tempfile.TemporaryDirectory() as temp_dir:
            repl = SlideDeckRepl(
                output_path=output_path,
                telemetry=telemetry,
                solution_code=solution_code,
                temp_dir=temp_dir,
                artifacts=artifacts
            )
            slide_kit = repl.scope["slide_kit"]

            logger.info(f"[Slide 1] Building Title & Domain Motivation Slide for '{plan.deck_title}'...")
            slide_kit.add_title_slide(repl.prs, title=plan.deck_title, subtitle=f"{plan.domain_subtitle} — Week {module.week}")
            built = 0
            for idx, spec in enumerate(plan.slides, 1):
                logger.info(f"[Slide {len(repl.prs.slides) + 1}] Building plan slide {idx}/{len(plan.slides)} [{spec.section}]: '{spec.title}'...")
                recipe_code = self._get_matching_recipe(spec.title, spec.visual.suggested_recipe_query or spec.visual.visual_idea)
                # Code only ever comes from the verified solution, and only on application slides
                function_name, excerpt = (solution_excerpt(solution_code, spec.code_function)
                                          if spec.section == "application" and spec.code_function else (None, ""))
                repl.scope.update(
                    slide_spec=spec,
                    code_function_name=function_name,
                    solution_excerpt=excerpt or "# (no verified code for this slide)",
                )
                builder_prompt = build_lesson_slide_prompt(
                    spec, plan, idx, recipe_code, artifacts=repl.artifacts, telemetry=telemetry,
                    code_function_name=function_name, solution_code_excerpt=excerpt,
                )
                try:
                    self._build_slide(
                        repl, SLIDE_BUILDER_SYSTEM, builder_prompt, f"Slide {idx} ('{spec.title}')",
                        trace=trace, artifact=f"slide_s{idx}", used=[plan_entity] if plan_entity else (),
                        review_focus=spec.teaching_point, speaker_notes=spec.speaker_notes,
                    )
                    built += 1
                except RuntimeError as err:
                    # One bad chart used to fail the whole week, whose code was already verified and saved
                    logger.warning(f"Skipping plan slide {idx}: {err}")

            if built < len(plan.slides) / 2:
                raise RuntimeError(f"Only {built} of {len(plan.slides)} planned slides could be built for '{plan.deck_title}'.")
            logger.info(f"[Slide {len(repl.prs.slides) + 1}] Adding Takeaways Slide...")
            slide_kit.add_card_slide(
                repl.prs,
                title="Key Takeaways",
                subtitle=plan.domain_subtitle,
                category="SUMMARY",
                cards=[{"title": f"Takeaway {i}", "body": t} for i, t in enumerate(plan.takeaways, 1)],
            )
            repl.prs.slides[-1].notes_slide.notes_text_frame.text = "\n".join(plan.takeaways)

            if not repl.finalize():
                logger.warning(f"Presentation deck could not be saved to {output_path}")
                return None
            logger.info(f"Successfully saved 16:9 presentation deck: {output_path} ({os.path.getsize(output_path)} bytes, {len(repl.prs.slides)} slides)")
            return output_path
