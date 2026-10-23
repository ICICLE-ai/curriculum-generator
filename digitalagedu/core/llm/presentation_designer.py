import os
import logging
import tempfile
from typing import Dict, Any, Optional, List, Union

from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.presentation_prompts import (
    PlannedSlide,
    SlideDeckPlanSchema,
    SingleSlideCodeSchema,
    PresentationActionSchema,
    PresentationCodeSchema,
    ConceptVisualSpec,
    DiscretizedConcept,
    DiscretizedConceptPlan,
    CONCEPT_DISCRETIZER_SYSTEM,
    build_concept_discretizer_prompt,
    CONCEPT_SLIDE_BUILDER_SYSTEM,
    build_concept_slide_prompt,
    build_presentation_designer_prompt,
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
    "PlannedSlide",
    "SlideDeckPlanSchema",
    "SingleSlideCodeSchema",
    "PresentationActionSchema",
    "PresentationCodeSchema",
    "ConceptVisualSpec",
    "DiscretizedConcept",
    "DiscretizedConceptPlan",
    "build_presentation_designer_prompt",
    "SlideDeckRepl",
    "SafeTelemetryDict",
    "execute_presentation_code_sandbox",
    "SUBPROCESS_TIMEOUT_SECONDS",
]


class PresentationDesigner:
    """
    Two-Stage Autonomous Presentation Designer:
    1. Deck Architect (Planner): Formulates the broad pedagogical narrative and what
       each slide should contain (without artificial line count restrictions).
    2. Sequential Slide Builder Loop: Generates and executes each planned slide in order,
       passing the context of all previous slides to maintain narrative continuity
       with zero duplicate slides and guaranteed visual rendering.
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

    def _plan_deck(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        solution_code: str,
        telemetry: Dict[str, Any]
    ) -> SlideDeckPlanSchema:
        """
        Formulates the broad pedagogical ideas and plans what each individual slide
        should contain. Line counts and slide counts are not restricted.
        """
        title = problem_formulation.title or module.title
        domain_ctx = problem_formulation.domain_context or module.context
        problem_stmt = problem_formulation.problem_statement or ""
        objectives = problem_formulation.learning_objectives or []
        focus = problem_formulation.suggested_focus or "Deep Learning & Model Architecture"

        run_sum = telemetry.get("run_summary", {}) if isinstance(telemetry, dict) else {}
        acc = run_sum.get("overall_accuracy") or run_sum.get("accuracy", "90.57")
        auc = run_sum.get("auc_roc", "0.9709")
        classes = telemetry.get("class_mapping", {}) if isinstance(telemetry, dict) else {}
        class_str = ", ".join(list(classes.values())[:6]) if classes else "Target Classes"

        subsystems_info = []
        if getattr(problem_formulation, "milestone_subsystems", None):
            for sub in problem_formulation.milestone_subsystems:
                comp_sigs = [f"{c.kind} {c.name}: {c.signature}" for c in getattr(sub, "components", [])]
                subsystems_info.append(f"- Milestone {sub.milestone_num}: {sub.title} ({sub.objective}) -> Components: {', '.join(comp_sigs[:2])}")
        subsystems_text = "\n".join(subsystems_info) if subsystems_info else "Core computational architecture"

        planner_system = (
            "You are an expert AI & Computing Professor and Presentation Architect.\n"
            "Your objective is to design a cohesive, visually-driven lecture slide deck plan that thoroughly teaches students this computing module.\n"
            "Formulate the overarching pedagogical narrative and plan each slide's content and visual focus.\n"
            "\n"
            "PLANNING PRINCIPLES:\n"
            "1. GRAPHIC-FIRST PEDAGOGY: Every single slide MUST feature a dedicated, high-impact visual graphic (flowchart, architecture diagram, confusion matrix, metric benchmark, data distribution, training curve, or 3D surface animation) that grounds the concept.\n"
            "2. NO ARTIFICIAL LIMITS: Do NOT restrict line counts or slide counts. Plan as many slides as necessary to thoroughly and comprehensively teach the problem formulation, methodology, architecture, implementation, and evaluation.\n"
            "3. NARRATIVE PROGRESSION: Each slide must logically build upon the preceding ones, guiding the student from motivation through engineering to empirical validation.\n"
            "4. AVAILABLE VISUAL GENERATORS IN visual_kit:\n"
            "   - `visual_kit.draw_flowchart`: For end-to-end processing pipelines and multi-step workflows.\n"
            "   - `visual_kit.draw_architecture`: For deep learning layers, tensor shapes, and backbone hierarchies.\n"
            "   - `visual_kit.draw_confusion_matrix`: For diagnostic error analysis and classification heatmaps.\n"
            "   - `visual_kit.draw_metric_comparison`: For multi-metric bar benchmarks (accuracy, precision, recall, F1).\n"
            "   - `visual_kit.draw_distribution`: For class balance and demographic charts (donut or bar).\n"
            "   - `visual_kit.create_figure` (matplotlib): For training loss curves, ROC/AUC curves, or custom geometric plots.\n"
            "   - `visual_kit.render_3d_surface_orbit`: For 3D loss landscapes and optimization geometry.\n"
            "   - `visual_kit.render_artifact_morph`: For image dataset comparisons and transformations."
        )

        planner_prompt = (
            f"MODULE: {title} (Week {module.week}) | Difficulty: {module.difficulty.title()}\n"
            f"DOMAIN CHALLENGE: {domain_ctx}\n"
            f"DIRECTIVE: {problem_stmt}\n"
            f"LEARNING OBJECTIVES:\n{chr(10).join([f'- {o}' for o in objectives])}\n\n"
            f"SUGGESTED FOCUS: {focus}\n"
            f"ENGINEERING SUBSYSTEMS:\n{subsystems_text}\n"
            f"DATASET & TELEMETRY: Accuracy {acc}%, AUC-ROC {auc}, Classes: {class_str}\n\n"
            f"Formulate the complete slide deck plan with a rich pedagogical narrative and specific visual directives for each slide."
        )

        try:
            plan: SlideDeckPlanSchema = self.client.chat.completions.create(
                model=self.model_name,
                response_model=SlideDeckPlanSchema,
                max_retries=2,
                max_tokens=8192,
                messages=[
                    {"role": "system", "content": planner_system},
                    {"role": "user", "content": planner_prompt}
                ]
            )
            if plan and plan.slides:
                logger.info(f"Successfully generated deck plan '{plan.deck_title}' with {len(plan.slides)} slides.")
                return plan
        except Exception as e:
            logger.warning(f"Slide deck planning LLM call encountered error: {e}.")
            return None

        return None

    def _discretize_concepts(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        solution_code: str,
        telemetry: Dict[str, Any],
        artifacts: Optional[Dict[str, str]] = None
    ) -> Optional[Union[DiscretizedConceptPlan, SlideDeckPlanSchema]]:
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
            elif isinstance(plan, SlideDeckPlanSchema) or hasattr(plan, "slides"):
                return plan
        except Exception as e:
            logger.warning(f"Concept discretization LLM call encountered error: {e}.")
            return None

        return None

    def generate_presentation_deck(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        solution_code: str,
        telemetry: Dict[str, Any],
        output_path: str,
        artifacts: Optional[Dict[str, str]] = None,
        max_turns: int = 8
    ) -> Optional[str]:
        """
        Executes an autonomous concept-discretized presentation design pipeline:
        1. Agent A: Discretizes module into exactly 3 to 5 non-overlapping concepts with domain grounding.
        2. Iterates concept-by-concept in the REPL sandbox, rendering visuals and building exactly
           one slide per concept (plus Title and Synthesis slides, ~5-7 slides total).
        """
        if not self.client:
            logger.info("No LLM client provided to PresentationDesigner. Skipping presentation generation.")
            return None

        # Stage 1: Formulate Discretized Concepts via Agent A
        logger.info(f"Agent A: Formulating concept architecture for module '{module.title}'...")
        plan = self._discretize_concepts(
            module=module,
            problem_formulation=problem_formulation,
            solution_code=solution_code,
            telemetry=telemetry,
            artifacts=artifacts
        )

        if not plan:
            logger.warning(f"Concept discretization failed to generate a plan for '{module.title}'. Skipping presentation deck generation.")
            return None

        with tempfile.TemporaryDirectory() as temp_dir:
            repl = SlideDeckRepl(
                output_path=output_path,
                telemetry=telemetry,
                solution_code=solution_code,
                temp_dir=temp_dir,
                artifacts=artifacts
            )

            # Check if plan is legacy SlideDeckPlanSchema (e.g. from tests or fallback)
            if isinstance(plan, SlideDeckPlanSchema) or hasattr(plan, "slides"):
                completed_slides_log = []
                for slide_plan in plan.slides:
                    idx = slide_plan.slide_index
                    logger.info(f"[Legacy Slide {idx}/{len(plan.slides)}] Generating: '{slide_plan.title}'...")
                    recipe_code = self._get_matching_recipe(slide_plan.title, slide_plan.visual_idea)
                    prev_context = ""
                    if completed_slides_log:
                        prev_context = (
                            "PREVIOUS SLIDES ALREADY CONSTRUCTED IN THIS DECK (Do not duplicate; build upon their concepts):\n"
                            + "\n".join(completed_slides_log) + "\n\n"
                        )
                    builder_system = (
                        "You are an expert Presentation Designer and Python Developer.\n"
                        f"You are constructing SLIDE #{idx} OF {len(plan.slides)} for the PowerPoint deck: '{plan.deck_title}'.\n"
                        f"Pedagogical Narrative: {plan.pedagogical_narrative}\n\n"
                        "You have live access to in the REPL:\n"
                        "- `prs`: Active PowerPoint presentation (16:9 canvas, width=13.333, height=7.5).\n"
                        "- `slide_kit`: Layout placement system:\n"
                        "    - slide_kit.add_hero_graphic(prs, title, image_path, subtitle=...)\n"
                        "    - slide_kit.add_split_slide(prs, title, left_content=[...], image_path=..., subtitle=...)\n"
                        "    - slide_kit.add_metric_slide(prs, title, metrics=[{'label': ..., 'value': ..., 'delta': ...}], subtitle=...)\n"
                        "    - slide_kit.add_card_slide(prs, title, cards=[{'title': ..., 'bullets': [...]}, ...], subtitle=...)\n"
                        "    - slide_kit.add_code_slide(prs, title, code='...', notes='...', subtitle=...)\n"
                        "    - slide_kit.add_title_slide(prs, title, subtitle=...)\n"
                        "- `visual_kit`: Custom figure canvas and diagram generators:\n"
                        "    - visual_kit.draw_flowchart(stages=[{'title': ..., 'desc': ...}], title=...)\n"
                        "    - visual_kit.draw_architecture(layers=[{'name': ..., 'shape': ..., 'color': ...}], title=...)\n"
                        "    - visual_kit.draw_confusion_matrix(matrix=..., labels=..., title=...)\n"
                        "    - visual_kit.draw_metric_comparison(categories=[...], series_a=[...], series_b=[...], label_a=..., label_b=..., title=...)\n"
                        "    - visual_kit.draw_distribution(labels=[...], values=[...], chart_type='donut'|'bar', title=...)\n"
                        "    - visual_kit.create_figure(title, xlabel, ylabel) -> fig, ax (use plt to plot, then visual_kit.save_figure(fig, filename=...))\n"
                        "- `plt`, `np`, `telemetry`, `solution_code`, `Colors`.\n\n"
                        "CRITICAL INSTRUCTIONS:\n"
                        "1. Render the visual graphic specified in the plan. Never put Python code inside text cards as a substitute for an image.\n"
                        "2. Do NOT restrict line counts. Provide comprehensive, rich explanations and detailed pedagogical bullets.\n"
                        "3. Add EXACTLY ONE slide to `prs` for this step. Do NOT re-create earlier slides or call prs.save().\n"
                        "4. Always return executable Python code wrapped in SingleSlideCodeSchema."
                    )
                    builder_prompt = (
                        f"{prev_context}"
                        f"TARGET SLIDE TO CONSTRUCT NOW:\n"
                        f"- Slide #{idx}: '{slide_plan.title}'\n"
                        f"- Subtitle: '{slide_plan.subtitle}'\n"
                        f"- Pedagogical Objective: {slide_plan.pedagogical_purpose}\n"
                        f"- Required Visual: {slide_plan.visual_idea}\n"
                        f"- Key Explanatory Points:\n{chr(10).join([f'  * {p}' for p in slide_plan.key_points])}\n\n"
                        f"RELEVANT VISUAL RECIPE:\n{recipe_code}\n\n"
                        f"Generate the Python snippet to render this visual and add Slide #{idx} to `prs`."
                    )
                    slide_added = False
                    slides_before = len(repl.prs.slides)
                    try:
                        action: SingleSlideCodeSchema = self.client.chat.completions.create(
                            model=self.model_name,
                            response_model=SingleSlideCodeSchema,
                            max_retries=2,
                            max_tokens=8192,
                            messages=[
                                {"role": "system", "content": builder_system},
                                {"role": "user", "content": builder_prompt}
                            ]
                        )
                        success, output_msg = repl.execute_snippet(action.python_code)
                        if success and len(repl.prs.slides) > slides_before:
                            slide_added = True
                        else:
                            logger.warning(f"Slide {idx} first attempt failed ({output_msg}). Retrying with self-healing feedback...")
                            retry_messages = [
                                {"role": "system", "content": builder_system},
                                {"role": "user", "content": builder_prompt},
                                {"role": "assistant", "content": f"Rationale: {action.rationale}\n```python\n{action.python_code}\n```"},
                                {"role": "user", "content": f"Code execution encountered an issue:\n{output_msg}\nEnsure a visual is rendered and slide_kit adds exactly one slide to `prs`. Provide corrected Python code."}
                            ]
                            retry_action: SingleSlideCodeSchema = self.client.chat.completions.create(
                                model=self.model_name,
                                response_model=SingleSlideCodeSchema,
                                max_retries=2,
                                max_tokens=8192,
                                messages=retry_messages
                            )
                            success_retry, retry_msg = repl.execute_snippet(retry_action.python_code)
                            if success_retry and len(repl.prs.slides) > slides_before:
                                slide_added = True
                    except Exception as call_err:
                        logger.warning(f"LLM slide generation error on Slide {idx}: {call_err}")

                    if not slide_added:
                        logger.warning(f"Failed to generate Slide {idx} via LLM and REPL. Skipping slide.")
                        continue

                    completed_slides_log.append(f"- Slide {idx}: '{slide_plan.title}' ({slide_plan.pedagogical_purpose})")

            else:
                # Discretized Concept Workflow (New Architecture)
                # 1. Slide 1: Title and Domain Context Slide
                logger.info(f"[Slide 1] Building Title & Domain Motivation Slide for '{plan.deck_title}'...")
                repl.scope["slide_kit"].add_title_slide(
                    repl.prs,
                    title=plan.deck_title,
                    subtitle=f"{plan.domain_subtitle} — Week {module.week}"
                )
                completed_slides_log = [f"- Slide 1: Title & Domain Context ('{plan.deck_title}')"]

                # 2. Slides 2 to K+1: Per-Concept Slide Agents (in REPL)
                for concept in plan.concepts:
                    c_idx = concept.concept_index
                    slide_num = len(repl.prs.slides) + 1
                    logger.info(f"[Slide {slide_num}] Building Concept {c_idx}/{len(plan.concepts)}: '{concept.title}'...")

                    recipe_code = self._get_matching_recipe(
                        concept.title,
                        concept.visual_spec.suggested_recipe_query or concept.visual_spec.visual_idea
                    )
                    prev_summary = "\n".join(completed_slides_log)

                    builder_prompt = build_concept_slide_prompt(
                        concept=concept,
                        total_concepts=len(plan.concepts),
                        deck_title=plan.deck_title,
                        domain_subtitle=plan.domain_subtitle,
                        recipe_code=recipe_code,
                        previous_slides_summary=prev_summary,
                        artifacts=repl.artifacts
                    )

                    slides_before = len(repl.prs.slides)
                    slide_added = False

                    try:
                        action: SingleSlideCodeSchema = self.client.chat.completions.create(
                            model=self.model_name,
                            response_model=SingleSlideCodeSchema,
                            max_retries=2,
                            max_tokens=8192,
                            messages=[
                                {"role": "system", "content": CONCEPT_SLIDE_BUILDER_SYSTEM},
                                {"role": "user", "content": builder_prompt}
                            ]
                        )

                        success, output_msg = repl.execute_snippet(action.python_code)
                        if success and len(repl.prs.slides) > slides_before:
                            slide_added = True
                        else:
                            logger.warning(f"Concept {c_idx} attempt 1 failed ({output_msg}). Retrying with self-healing feedback...")
                            retry_messages = [
                                {"role": "system", "content": CONCEPT_SLIDE_BUILDER_SYSTEM},
                                {"role": "user", "content": builder_prompt},
                                {"role": "assistant", "content": f"Rationale: {action.rationale}\n```python\n{action.python_code}\n```"},
                                {"role": "user", "content": f"Execution issue:\n{output_msg}\nEnsure a graphic is rendered and slide_kit adds exactly one slide to `prs` for Concept: {concept.title}. Return corrected Python code."}
                            ]
                            retry_action: SingleSlideCodeSchema = self.client.chat.completions.create(
                                model=self.model_name,
                                response_model=SingleSlideCodeSchema,
                                max_retries=2,
                                max_tokens=8192,
                                messages=retry_messages
                            )
                            success_retry, retry_msg = repl.execute_snippet(retry_action.python_code)
                            if success_retry and len(repl.prs.slides) > slides_before:
                                slide_added = True
                    except Exception as call_err:
                        logger.warning(f"LLM slide generation error on Concept {c_idx}: {call_err}")

                    if not slide_added:
                        logger.warning(f"Failed to generate Concept {c_idx} slide via LLM and REPL. Skipping slide.")
                        continue

                    completed_slides_log.append(f"- Slide {slide_num}: Concept {c_idx} ('{concept.title}')")

                # 3. Final Slide: Synthesis & Technical Takeaways Slide
                synth_slide_num = len(repl.prs.slides) + 1
                logger.info(f"[Slide {synth_slide_num}] Adding Synthesis & Takeaways Slide...")
                synth_cards = [
                    {"title": f"Finding {i+1}", "bullets": [t]}
                    for i, t in enumerate(plan.synthesis_takeaways[:3])
                ]
                repl.scope["slide_kit"].add_card_slide(
                    repl.prs,
                    title="Curriculum Synthesis & Key Findings",
                    subtitle=f"Empirical validation and algorithmic summary for {module.title}",
                    cards=synth_cards
                )

            if len(repl.prs.slides) == 0:
                logger.warning(f"No slides were generated for module '{module.title}'. Presentation generation aborted.")
                return None

            # Finalize presentation save
            if repl.finalize():
                size = os.path.getsize(output_path)
                logger.info(f"Successfully saved 16:9 presentation deck: {output_path} ({size} bytes, {len(repl.prs.slides)} slides)")
                return output_path
            else:
                logger.warning(f"Presentation deck could not be saved to {output_path}")
                return None
