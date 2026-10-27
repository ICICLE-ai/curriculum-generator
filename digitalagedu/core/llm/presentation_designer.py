import os
import logging
import tempfile
from typing import Dict, Any, Optional

from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.presentation_prompts import (
    SingleSlideCodeSchema,
    ConceptVisualSpec,
    DiscretizedConcept,
    DiscretizedConceptPlan,
    CONCEPT_DISCRETIZER_SYSTEM,
    build_concept_discretizer_prompt,
    CONCEPT_SLIDE_BUILDER_SYSTEM,
    build_concept_slide_prompt,
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
    "SingleSlideCodeSchema",
    "ConceptVisualSpec",
    "DiscretizedConcept",
    "DiscretizedConceptPlan",
    "SlideDeckRepl",
    "SafeTelemetryDict",
    "execute_presentation_code_sandbox",
    "SUBPROCESS_TIMEOUT_SECONDS",
]


class PresentationDesigner:
    """
    Two-Stage Autonomous Presentation Designer:
    1. Concept Discretizer (Agent A): splits the module into 3-5 non-overlapping concepts.
    2. Sequential Slide Builder Loop: generates and executes one slide per concept in a stateful
       REPL, passing the summary of previous slides to maintain narrative continuity.
    """

    def __init__(self, client: Any = None, model_name: Optional[str] = None):
        self.client = client
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

    def _build_slide(self, repl: SlideDeckRepl, system: str, prompt: str, label: str) -> None:
        """Asks the LLM for one slide's code, runs it, retries once with the error; raises if no slide was added."""
        slides_before = len(repl.prs.slides)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": prompt}]
        try:
            for attempt in (1, 2):
                action: SingleSlideCodeSchema = self.client.chat.completions.create(
                    model=self.model_name,
                    response_model=SingleSlideCodeSchema,
                    max_retries=2,
                    max_tokens=8192,
                    messages=messages
                )
                success, output_msg = repl.execute_snippet(action.python_code)
                if success and len(repl.prs.slides) > slides_before:
                    return
                if attempt == 1:
                    logger.warning(f"{label} attempt 1 failed ({output_msg}). Retrying with self-healing feedback...")
                    messages += [
                        {"role": "assistant", "content": f"Rationale: {action.rationale}\n```python\n{action.python_code}\n```"},
                        {"role": "user", "content": f"Execution issue:\n{output_msg}\nEnsure a graphic is rendered and slide_kit adds exactly one slide to `prs` for {label}. Return corrected Python code."}
                    ]
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
        artifacts: Optional[Dict[str, str]] = None
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
                builder_prompt = build_concept_slide_prompt(
                    concept=concept,
                    total_concepts=len(plan.concepts),
                    deck_title=plan.deck_title,
                    domain_subtitle=plan.domain_subtitle,
                    recipe_code=recipe_code,
                    previous_slides_summary="\n".join(completed_slides_log),
                    artifacts=repl.artifacts
                )
                self._build_slide(repl, CONCEPT_SLIDE_BUILDER_SYSTEM, builder_prompt, f"Concept {c_idx} ('{concept.title}')")
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
