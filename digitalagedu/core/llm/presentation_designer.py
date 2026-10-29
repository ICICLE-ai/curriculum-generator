import os
import re
import logging
import tempfile
from typing import Dict, Any, Optional, Sequence

from digitalagedu.core.llm.ai_setup import ask_code
from digitalagedu.core.llm.generation_trace import now_iso
from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.presentation_prompts import (
    ConceptVisualSpec,
    DiscretizedConcept,
    DiscretizedConceptPlan,
    CONCEPT_DISCRETIZER_SYSTEM,
    build_concept_discretizer_prompt,
    CONCEPT_SLIDE_BUILDER_SYSTEM,
    build_concept_slide_prompt,
    solution_excerpt,
    SUBPROCESS_TIMEOUT_SECONDS,
)
from digitalagedu.core.llm.slide_deck_repl import (
    SafeTelemetryDict,
    SlideDeckRepl,
    execute_presentation_code_sandbox,
)

logger = logging.getLogger(__name__)

# Re-exports for backward compatibility
__all__ = [
    "PresentationDesigner",
    "ConceptVisualSpec",
    "DiscretizedConcept",
    "DiscretizedConceptPlan",
    "SlideDeckRepl",
    "SafeTelemetryDict",
    "execute_presentation_code_sandbox",
    "SUBPROCESS_TIMEOUT_SECONDS",
]


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
    1. Concept Discretizer (Agent A): splits the module into 3-5 non-overlapping concepts.
    2. Sequential Slide Builder Loop: generates and executes one slide per concept in a stateful
       REPL, passing the summary of previous slides to maintain narrative continuity.
    """

    def __init__(self, client: Any = None, model_name: Optional[str] = None, code_client: Any = None):
        self.client = client  # instructor client: structured concept plan
        self.code_client = code_client  # plain OpenAI client: slide code as fenced python blocks
        self.model_name = model_name or os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-Coder-14B-Instruct")

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

    def _discretize_concepts(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        solution_code: str,
        telemetry: Dict[str, Any],
        artifacts: Optional[Dict[str, str]] = None
    ) -> Optional[DiscretizedConceptPlan]:
        """
        Agent A: Analyzes the full module and reference solution to discretize it
        into 3 to 5 mutually exclusive, non-overlapping core concepts.
        """
        if not self.client:
            return None

        prompt = build_concept_discretizer_prompt(
            module=module,
            problem_formulation=problem_formulation,
            solution_code=solution_code,
            telemetry=telemetry,
            artifacts=artifacts
        )

        try:
            plan = self.client.chat.completions.create(
                model=self.model_name,
                response_model=DiscretizedConceptPlan,
                max_retries=2,
                max_tokens=8192,
                messages=[
                    {"role": "system", "content": CONCEPT_DISCRETIZER_SYSTEM},
                    {"role": "user", "content": prompt}
                ]
            )
            if plan and getattr(plan, "concepts", None) and len(plan.concepts) >= 3:
                plan.concepts = plan.concepts[:5]
                logger.info(f"Agent A: Successfully discretized '{plan.deck_title}' into {len(plan.concepts)} concepts.")
                return plan
        except Exception as e:
            logger.warning(f"Concept discretization LLM call encountered error: {e}.")
        return None

    def _build_slide(self, repl: SlideDeckRepl, system: str, prompt: str, label: str,
                     trace=None, artifact: str = "slide_code", used=(),
                     required_text: Sequence[str] = (), speaker_notes: str = "") -> None:
        """Asks the LLM for one slide's code, runs it, retries once with the error; raises if no slide was added.
        Code that fabricates data is rejected unrun; a slide missing any `required_text` (e.g. the verified
        function name, a real number) is removed and retried. With a GenerationTrace, each code version and
        REPL execution is recorded as PROV entities/activities."""
        slides_before = len(repl.prs.slides)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        exec_activity = None
        try:
            for attempt in (1, 2):
                code = ask_code(
                    self.code_client, self.model_name, messages, f"{label} slide code", max_tokens=8192,
                    trace=trace, agent="slide_builder", artifact=artifact,
                    purpose="generate" if attempt == 1 else "slide_exec_retry", used=used, informed_by=exec_activity,
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
                        output_msg = (f"The slide is missing required content: {missing}. Keep the layout template's "
                                      f"code box (solution_excerpt / code_function_name) and evidence metric cards.")
                    elif speaker_notes:
                        repl.prs.slides[-1].notes_slide.notes_text_frame.text = speaker_notes
                if trace is not None:
                    exec_activity = trace.add_activity(
                        "slide_exec", "slide_repl", start=start, label=label, success=success,
                        slide_added=slide_added, error=None if success else str(output_msg)[-2000:],
                    )
                    trace.relate("used", activity=exec_activity, entity=trace.latest[artifact])
                if success and slide_added:
                    return
                if attempt == 1:
                    logger.warning(f"{label} attempt 1 failed ({output_msg}). Retrying with self-healing feedback...")
                    # ask_code already appended this attempt's reply to messages
                    messages.append({"role": "user", "content": f"Execution issue:\n{output_msg}\nEnsure a graphic is rendered and slide_kit adds exactly one slide to `prs` for {label}. Return corrected Python code."})
        except Exception as call_err:
            logger.warning(f"LLM slide generation error on {label}: {call_err}")
        raise RuntimeError(f"Failed to generate {label} slide after self-healing retry.")

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
        Executes the concept-discretized presentation design pipeline:
        title slide, one REPL-built slide per concept, then a synthesis slide.
        """
        if not self.client:
            logger.info("No LLM client provided to PresentationDesigner. Skipping presentation generation.")
            return None

        logger.info(f"Agent A: Formulating concept architecture for module '{module.title}'...")
        plan = self._discretize_concepts(
            module=module,
            problem_formulation=problem_formulation,
            solution_code=solution_code,
            telemetry=telemetry,
            artifacts=artifacts
        )
        if not plan:
            raise RuntimeError(f"Concept discretization failed to generate a plan for '{module.title}'.")
        plan_entity = None
        if trace is not None:
            plan_entity = trace.add_entity("concept_plan", plan.model_dump_json(indent=2), ext="json")
            trace.relate("wasAttributedTo", entity=plan_entity, agent=trace.agent("concept_discretizer"))
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
            completed_slides_log = [f"- Slide 1: Title & Domain Context ('{plan.deck_title}')"]

            for concept in plan.concepts:
                c_idx = concept.concept_index
                slide_num = len(repl.prs.slides) + 1
                logger.info(f"[Slide {slide_num}] Building Concept {c_idx}/{len(plan.concepts)}: '{concept.title}'...")
                recipe_code = self._get_matching_recipe(
                    concept.title,
                    concept.visual_spec.suggested_recipe_query or concept.visual_spec.visual_idea
                )
                # The template fills the slide's text from the plan and its code box from the verified solution
                function_name, excerpt = solution_excerpt(solution_code, concept.code_function)
                repl.scope.update(
                    concept=concept,
                    code_function_name=function_name or concept.code_function,
                    solution_excerpt=excerpt or "# (no matching function in the verified solution)",
                )
                builder_prompt = build_concept_slide_prompt(
                    concept=concept,
                    total_concepts=len(plan.concepts),
                    deck_title=plan.deck_title,
                    domain_subtitle=plan.domain_subtitle,
                    recipe_code=recipe_code,
                    previous_slides_summary="\n".join(completed_slides_log),
                    artifacts=repl.artifacts,
                    telemetry=telemetry,
                    code_function_name=function_name,
                )
                self._build_slide(
                    repl, CONCEPT_SLIDE_BUILDER_SYSTEM, builder_prompt, f"Concept {c_idx} ('{concept.title}')",
                    trace=trace, artifact=f"slide_c{c_idx}", used=[plan_entity] if plan_entity else (),
                    required_text=[function_name, concept.real_evidence[0].value],
                    speaker_notes=(f"{concept.speaker_notes}\n\nRule: {concept.formula_or_rule}\n"
                                   f"Common misconception: {concept.misconception}"),
                )
                completed_slides_log.append(f"- Slide {slide_num}: Concept {c_idx} ('{concept.title}')")

            logger.info(f"[Slide {len(repl.prs.slides) + 1}] Adding Synthesis & Takeaways Slide...")
            slide_kit.add_card_slide(
                repl.prs,
                title="Curriculum Synthesis & Key Findings",
                subtitle=f"Empirical validation and algorithmic summary for {module.title}",
                cards=[{"title": f"Finding {i+1}", "bullets": [t]} for i, t in enumerate(plan.synthesis_takeaways[:3])]
            )

            if not repl.finalize():
                logger.warning(f"Presentation deck could not be saved to {output_path}")
                return None
            logger.info(f"Successfully saved 16:9 presentation deck: {output_path} ({os.path.getsize(output_path)} bytes, {len(repl.prs.slides)} slides)")
            return output_path
