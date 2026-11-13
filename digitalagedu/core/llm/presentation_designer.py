import os
import re
import logging
import shutil
import tempfile
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Dict, Any, List, Optional, Sequence

from pptx import Presentation

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
    overlong_texts,
    get_text,
    set_text,
    ShortenedTexts,
    SHORTEN_SYSTEM,
    build_shorten_prompt,
    SlideSplit,
    SPLIT_SYSTEM,
    build_split_prompt,
)
from digitalagedu.core.llm.slide_deck_repl import (
    SafeTelemetryDict,
    SlideDeckRepl,
    execute_presentation_code_sandbox,
)
from digitalagedu.core.llm.slide_render import render_deck_pngs
from digitalagedu.core.llm.slide_kit.theme import describe_shapes, layout_issues

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
# Reviews that may send a slide back for an edit; the last edit is reviewed too, and the best-reviewed version is kept
MAX_SLIDE_REVIEW_ROUNDS = 4
SLIDE_PREFETCH_WORKERS = 4  # first-attempt slide code requested at once; ai_setup.MODEL_SLOTS caps what actually runs

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
        self._accepted_shots: List[str] = []  # screenshots of this deck's accepted (or kept) slides
        self._shots_taken = 0
        self._last_shot: Optional[str] = None  # screenshot behind the latest review

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
                max_retries=3,  # re-asked when the flow, method depth or code placement is off
                max_tokens=65536,
                messages=[{"role": "system", "content": LESSON_PLANNER_SYSTEM}, {"role": "user", "content": prompt}],
                **llm_kwargs(self.plan_model),
            )
            log_llm(f"Lesson plan '{plan.deck_title}': {len(plan.slides)} slides, methods {plan.methods}")
        except Exception as e:
            logger.warning(f"Lesson planning LLM call encountered error: {e}.")
            return None
        self._shorten_texts(plan)
        return plan

    def _shorten_texts(self, plan: LessonPlan) -> None:
        """Rewrites planned texts longer than their slide box in one call. Never cuts them: a text the call leaves
        too long (or a failed call) stays whole, and slide_kit grows its box."""
        found = overlong_texts(plan)
        if not found:
            return
        items = [(get_text(owner, field, i), limit) for owner, field, i, limit in found]
        try:
            reply = self.client.chat.completions.create(
                model=self.plan_model, response_model=ShortenedTexts, max_retries=1, max_tokens=8192,
                messages=[{"role": "system", "content": SHORTEN_SYSTEM}, {"role": "user", "content": build_shorten_prompt(items)}],
                **llm_kwargs(self.plan_model),
            )
        except Exception as err:
            logger.warning(f"Shortening {len(found)} over-long slide texts failed; keeping them whole: {err}")
            return
        fixed = 0
        for (owner, field, i, limit), (old, _), new in zip(found, items, reply.texts):
            new = new.strip()
            if new and len(new) < len(old) and not new.endswith(("...", "…")):
                set_text(owner, field, i, new)
                fixed += len(new) <= limit
        log_llm(f"Shortened slide texts: {fixed} of {len(found)} now fit their boxes")

    def _split_slide(self, spec: LessonSlide) -> Optional[List[LessonSlide]]:
        """Two slides that together carry `spec`'s content, for a slide whose content does not fit one; None if
        the call fails. Section, method and code stay the planner's; evidence must be the slide's own numbers."""
        try:
            split = self.client.chat.completions.create(
                model=self.plan_model, response_model=SlideSplit, max_retries=2, max_tokens=16384,
                messages=[{"role": "system", "content": SPLIT_SYSTEM}, {"role": "user", "content": build_split_prompt(spec)}],
                **llm_kwargs(self.plan_model),
            )
        except Exception as err:
            logger.warning(f"Splitting slide '{spec.title}' failed: {err}")
            return None
        real = {e.value for e in spec.evidence}
        halves = [split.first, split.second]
        coded = [h for h in halves if h.code_function]
        for half in halves:
            half.section, half.method, half.code_function = spec.section, spec.method, None
            half.evidence = [e for e in half.evidence if e.value in real]
        if spec.code_function:  # the verified code appears once, on the half the split chose (else the second)
            (coded[0] if coded else halves[-1]).code_function = spec.code_function
        if spec.section in ("goal", "application"):
            for half in halves:
                half.evidence = half.evidence or spec.evidence[:1]  # these slides always show a real number
        return halves

    def _replace_with_split(self, repl: SlideDeckRepl, spec: LessonSlide, plan: LessonPlan, idx: int,
                            solution_code: str, telemetry: Dict[str, Any], trace, used) -> None:
        """Last resort for a slide still crowded after its reviews (the deck's newest slide): rebuilds its content as
        two slides and drops it. The halves are built once, never split again; if either fails, the original stays,
        so no content is lost."""
        halves = self._split_slide(spec)
        if not halves:
            return
        log_llm(f"Slide {idx} ('{spec.title}') still crowded after {MAX_SLIDE_REVIEW_ROUNDS} reviews; splitting it in two")
        original = len(repl.prs.slides) - 1
        try:
            for part, half in zip("ab", halves):
                function_name, excerpt = (solution_excerpt(solution_code, half.code_function)
                                          if half.section == "application" and half.code_function else (None, ""))
                repl.scope.update(slide_spec=half, code_function_name=function_name,
                                  solution_excerpt=excerpt or "# (no verified code for this slide)")
                recipe = self._get_matching_recipe(half.title, half.visual.suggested_recipe_query or half.visual.visual_idea)
                prompt = build_lesson_slide_prompt(half, plan, idx, recipe, artifacts=repl.artifacts, telemetry=telemetry,
                                                   code_function_name=function_name, solution_code_excerpt=excerpt)
                self._build_slide(repl, SLIDE_BUILDER_SYSTEM, prompt, f"Slide {idx}{part} ('{half.title}')",
                                  trace=trace, artifact=f"slide_s{idx}{part}", used=used,
                                  review_focus=half.teaching_point, speaker_notes=half.speaker_notes)
        except RuntimeError as err:
            logger.warning(f"Keeping the crowded slide {idx}: its split could not be built ({err})")
            repl._drop_slides_from(original + 1)
            return
        repl._drop_slide(original)

    def _build_slide(self, repl: SlideDeckRepl, system: str, prompt: str, label: str,
                     trace=None, artifact: str = "slide_code", used=(),
                     required_text: Sequence[str] = (), speaker_notes: str = "", review_focus: str = "",
                     prefetched: Optional[Future] = None) -> bool:
        """Asks the LLM for one slide's code and runs it, then improves that slide in place: the vision reviewer's
        fixes go back as edits to the live slide (up to MAX_SLIDE_REVIEW_ROUNDS), not as a rewrite. Every rewrite fixed
        the named problems and moved everything else, so no slide ever passed (run ab697516). Every version is
        reviewed, and the one with the fewest blocking issues is kept. A build or edit that fails to run is retried
        with the error (up to MAX_SLIDE_EXEC_FAILURES in all). Raises if no slide was added. Returns False when the
        kept slide still has overlapping or off-slide elements. Code that fabricates data is rejected unrun; a
        version missing any `required_text` is undone and retried. With a GenerationTrace, each code version, REPL
        execution and review is recorded as PROV activities."""
        slides_before = len(repl.prs.slides)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        exec_activity, purpose = None, "generate"
        failures = reviews = 0
        steps: List[str] = []  # the code that built the slide, then each edit kept on it
        best = None  # (blocking issues, steps that give that version, its screenshot)
        try:
            while failures < MAX_SLIDE_EXEC_FAILURES:
                code = None
                if prefetched is not None:
                    # The first attempt was requested at deck start, alongside the other slides'
                    pending, prefetched = prefetched, None
                    try:
                        code, messages = pending.result()
                    except Exception as err:
                        logger.warning(f"{label} prefetched slide code failed ({err}); asking again")
                if code is None:
                    code = ask_code(
                        self.code_client, self.model_name, messages, f"{label} slide {'edit' if steps else 'code'}",
                        max_tokens=16384, trace=trace, agent="slide_builder", artifact=artifact,
                        purpose=purpose, used=used, informed_by=exec_activity,
                    )
                start = now_iso()
                fabricated = synthetic_data_issue(code)
                if fabricated:
                    success, output_msg = False, fabricated
                elif steps:
                    success, output_msg = repl.execute_edit(code, steps)
                else:
                    success, output_msg = repl.execute_snippet(code)
                slide_added = len(repl.prs.slides) > slides_before
                if success and slide_added:
                    slide_text = " ".join(
                        sh.text_frame.text for s in list(repl.prs.slides)[slides_before:] for sh in s.shapes if sh.has_text_frame
                    )
                    missing = [t for t in required_text if t and t not in slide_text]
                    if missing:
                        if steps:
                            repl.restore_slide(steps)
                        else:
                            repl._drop_slides_from(slides_before)
                        success = False
                        slide_added = bool(steps)
                        output_msg = f"The slide is missing required content: {missing}."
                if trace is not None:
                    exec_activity = trace.add_activity(
                        "slide_exec", "slide_repl", start=start, label=label, success=success,
                        slide_added=slide_added, error=None if success else str(output_msg)[-2000:],
                    )
                    trace.relate("used", activity=exec_activity, entity=trace.latest[artifact])
                # ask_code already appended this attempt's reply to messages
                if success and slide_added:
                    steps.append(code)
                    issues = self._review_slide(repl, label, review_focus, trace)
                    if best is None or len(issues) < len(best[0]):
                        best = (issues, list(steps), self._last_shot)
                    if issues and reviews < MAX_SLIDE_REVIEW_ROUNDS:
                        reviews += 1
                        purpose = "slide_review_revision"
                        messages.append({"role": "user", "content": self._edit_request(repl, issues)})
                        continue
                    return self._keep_best(repl, label, steps, best, speaker_notes)
                failures += 1
                purpose = "slide_exec_retry"
                if failures < MAX_SLIDE_EXEC_FAILURES:
                    logger.warning(f"{label} attempt failed ({output_msg}). Retrying with self-healing feedback...")
                    if steps:
                        messages.append({"role": "user", "content": (
                            f"Your edit did not work:\n{output_msg}\nReturn corrected code that edits `prs.slides[-1]` "
                            "in place for the same fixes; do not add a slide.")})
                    else:
                        messages.append({"role": "user", "content": f"Execution issue:\n{output_msg}\nEnsure a graphic is rendered and slide_kit adds exactly one slide to `prs` for {label}. Return corrected Python code."})
            if steps:  # edits kept failing; the slide is still there, so keep its best reviewed version
                return self._keep_best(repl, label, steps, best, speaker_notes)
        except Exception as call_err:
            logger.warning(f"LLM slide generation error on {label}: {call_err}")
            if steps and len(repl.prs.slides) > slides_before:
                return self._keep_best(repl, label, steps, best, speaker_notes)
        raise RuntimeError(f"Failed to generate {label} slide after {MAX_SLIDE_EXEC_FAILURES} failed attempts.")

    @staticmethod
    def _edit_request(repl: SlideDeckRepl, issues: List[str]) -> str:
        """The reviewer's fixes, as a request to edit the live slide: its shapes are listed by index, so the
        builder changes only what the fixes name."""
        shapes = "\n".join(describe_shapes(repl.prs.slides[-1]))
        return ("A reviewer looked at a screenshot of your slide and asks for these fixes:\n"
                + "\n".join(f"- {i}" for i in issues)
                + "\n\nThe slide is still in the deck as `slide = prs.slides[-1]`. Its shapes, by index into `slide.shapes`:\n"
                + shapes
                + "\n\nWrite code that EDITS this slide in place and changes only what the fixes name:\n"
                  "- move or resize a shape: `shape.left = Inches(...)`, `.top`, `.width`, `.height`\n"
                  "- shorten or replace a text: `slide_kit.replace_text(shape, new_text)` (keeps its font)\n"
                  "- re-plot a chart: save a new PNG, remove the old picture (`pic._element.getparent().remove(pic._element)`), "
                  "then `slide_kit.add_image(slide, x, y, w, h, image_path=...)` in its box\n"
                  "Do not add a slide, do not change the font size of text that is too long (shorten it), and do not "
                  "rebuild the parts that already work.")

    def _keep_best(self, repl: SlideDeckRepl, label: str, steps: List[str], best, speaker_notes: str) -> bool:
        """Leaves the best-reviewed version of the deck's last slide in place, adds its speaker notes, and returns
        whether it is free of overlapping and off-slide elements (False sends it to the split path)."""
        issues, best_steps, shot = best
        if len(best_steps) < len(steps):
            log_llm(f"{label}: kept the best version ({len(issues)} fixes open, after {len(best_steps) - 1} edits) "
                    f"instead of the last of {len(steps) - 1} edits")
            repl.restore_slide(best_steps)
            steps[:] = best_steps
        if shot and shot not in self._accepted_shots:
            self._accepted_shots.append(shot)  # kept slides count for the reviewer's variety check too
        if speaker_notes:
            repl.prs.slides[-1].notes_slide.notes_text_frame.text = speaker_notes
        return not layout_issues(repl.prs.slides[-1])

    def _first_attempt(self, system: str, prompt: str, label: str, trace, artifact: str, used) -> tuple:
        """A slide's first code attempt, run on a prefetch thread: (code, the conversation it extends)."""
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        code = ask_code(self.code_client, self.model_name, messages, f"{label} slide code", max_tokens=16384,
                        trace=trace, agent="slide_builder", artifact=artifact, purpose="generate", used=used)
        return code, messages

    def _screenshot_last_slide(self, repl: SlideDeckRepl, label: str) -> Optional[str]:
        """PNG of the deck's newest slide, or None when rendering is unavailable. Only that slide is rendered:
        converting the whole deck for every review overran LibreOffice's timeout on Expanse (run 0ffa9ff2)."""
        # In the job folder, not the node's /tmp: LibreOffice could not write its PDF there on Expanse
        # (0x507 Io Access, run 49088b7e); the screenshots also stay with the job for inspection
        review_dir = os.path.join(os.getcwd(), "tmp", "slide_review",
                                  os.path.splitext(os.path.basename(repl.output_path))[0])
        os.makedirs(review_dir, exist_ok=True)
        deck = os.path.join(review_dir, "review_slide.pptx")
        repl.prs.save(deck)
        one = Presentation(deck)
        slide_ids = one.slides._sldIdLst
        for sid in list(slide_ids)[:-1]:
            slide_ids.remove(sid)
            one.part.drop_rel(sid.rId)  # unreferenced slides and their images are then left out of the file
        one.save(deck)
        pngs = render_deck_pngs(deck, review_dir)
        if not pngs:
            return None
        self._shots_taken += 1
        shot = os.path.join(review_dir, f"shot_{self._shots_taken:03d}.png")
        shutil.copyfile(pngs[-1], shot)  # the renderer reuses its file names
        return shot

    def _review_slide(self, repl: SlideDeckRepl, label: str, focus: str, trace=None) -> List[str]:
        """Fixes for the deck's last slide: overlapping or off-slide elements from shape geometry (always), plus
        the vision reviewer's verdict on a rendered screenshot shown next to the earlier slides for variety.
        The vision part is skipped without a client or renderer, or on a reviewer error: a review must never
        cost the slide. Returns [] when the slide is accepted."""
        start = now_iso()
        issues = layout_issues(repl.prs.slides[-1])
        polish: List[str] = []
        shot = self._screenshot_last_slide(repl, label) if self.client is not None else None
        self._last_shot = shot
        if shot:
            try:
                review = self.client.chat.completions.create(
                    model=self.reviewer_model, response_model=SlideReview, max_retries=2, max_tokens=8192,
                    messages=build_slide_review_messages(label, focus, image_url(shot), [image_url(p) for p in self._accepted_shots[-3:]]),
                    **llm_kwargs(self.reviewer_model),
                )
                # Only concrete blocking issues send the slide back: a bare "not acceptable" sent back
                # "Improve the slide's readability." and every slide was rejected every round (run ab697516)
                issues += [i for i in review.issues if i.strip()]
                polish = [p for p in review.polish if p.strip()]
            except Exception as err:
                logger.warning(f"Slide review failed for {label}, keeping the slide: {err}")
            if not issues:
                self._accepted_shots.append(shot)  # earlier slides shown to later reviews, for variety
        log_llm(f"{label} review ({'screenshot + geometry' if shot else 'geometry only'}): "
                + ("accepted" if not issues else f"{len(issues)} fixes: " + " | ".join(issues))[:600]
                + (f" (polish, not sent back: {len(polish)})" if polish else ""))
        if trace is not None:
            trace.add_activity("slide_review", "slide_reviewer", start=start, label=label, model=self.reviewer_model,
                               acceptable=not issues, issues=issues, polish=polish)
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

        self._accepted_shots = []
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
            # Each slide's prompt is self-contained (it carries the deck outline), so every first attempt is requested
            # up front and generated in parallel (capped per model by ai_setup.MODEL_SLOTS); slides are then built,
            # run and reviewed in order, so retries and revisions stay one conversation per slide.
            jobs = []
            for idx, spec in enumerate(plan.slides, 1):
                recipe_code = self._get_matching_recipe(spec.title, spec.visual.suggested_recipe_query or spec.visual.visual_idea)
                # Code only ever comes from the verified solution, and only on application slides
                function_name, excerpt = (solution_excerpt(solution_code, spec.code_function)
                                          if spec.section == "application" and spec.code_function else (None, ""))
                builder_prompt = build_lesson_slide_prompt(
                    spec, plan, idx, recipe_code, artifacts=repl.artifacts, telemetry=telemetry,
                    code_function_name=function_name, solution_code_excerpt=excerpt,
                )
                jobs.append((idx, spec, function_name, excerpt, builder_prompt))

            built = 0
            with ThreadPoolExecutor(max_workers=SLIDE_PREFETCH_WORKERS) as pool:
                used = [plan_entity] if plan_entity else []
                prefetched = {idx: pool.submit(self._first_attempt, SLIDE_BUILDER_SYSTEM, prompt,
                                               f"Slide {idx} ('{spec.title}')", trace, f"slide_s{idx}", used)
                              for idx, spec, _, _, prompt in jobs}
                for idx, spec, function_name, excerpt, builder_prompt in jobs:
                    logger.info(f"[Slide {len(repl.prs.slides) + 1}] Building plan slide {idx}/{len(plan.slides)} [{spec.section}]: '{spec.title}'...")
                    repl.scope.update(
                        slide_spec=spec,
                        code_function_name=function_name,
                        solution_excerpt=excerpt or "# (no verified code for this slide)",
                    )
                    try:
                        fits = self._build_slide(
                            repl, SLIDE_BUILDER_SYSTEM, builder_prompt, f"Slide {idx} ('{spec.title}')",
                            trace=trace, artifact=f"slide_s{idx}", used=used,
                            review_focus=spec.teaching_point, speaker_notes=spec.speaker_notes,
                            prefetched=prefetched[idx],
                        )
                        built += 1
                    except RuntimeError as err:
                        # One bad chart used to fail the whole week, whose code was already verified and saved
                        logger.warning(f"Skipping plan slide {idx}: {err}")
                        continue
                    if not fits:
                        self._replace_with_split(repl, spec, plan, idx, solution_code, telemetry, trace, used)

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
