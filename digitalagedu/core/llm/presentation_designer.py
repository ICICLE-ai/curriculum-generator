import os
import logging
import tempfile
from typing import Dict, Any, Optional

from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.presentation_prompts import (
    PlannedSlide,
    SlideDeckPlanSchema,
    SingleSlideCodeSchema,
    PresentationActionSchema,
    PresentationCodeSchema,
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

        # Local fallback from VISUAL_RECIPES
        try:
            from digitalagedu.core.llm.visuals.visual_recipes import VISUAL_RECIPES
            query_lower = query.lower()
            for r in VISUAL_RECIPES:
                if any(t in query_lower for t in r["topics"]):
                    return r["text"]
            return VISUAL_RECIPES[0]["text"]
        except Exception:
            return ""

    def _build_default_plan(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        telemetry: Dict[str, Any]
    ) -> SlideDeckPlanSchema:
        """Deterministic default slide deck plan if LLM planning fails."""
        title = problem_formulation.title or module.title
        domain_ctx = problem_formulation.domain_context or module.context
        objectives = problem_formulation.learning_objectives or []

        slides = [
            PlannedSlide(
                slide_index=1,
                title=f"{title}: Overview & Problem Formulation",
                subtitle="Clinical and Computational Domain Motivation",
                pedagogical_purpose="Introduce domain context, clinical challenges, and computational goals.",
                visual_idea="Hero graphic displaying authentic dataset sample inspection or problem overview.",
                key_points=[domain_ctx[:200] if domain_ctx else "Domain context and motivation"] + [f"Objective: {o}" for o in objectives[:2]]
            ),
            PlannedSlide(
                slide_index=2,
                title="End-to-End Processing & Workflow Pipeline",
                subtitle="Architectural Stages from Raw Inputs to Predictions",
                pedagogical_purpose="Explain data normalization, spatial feature engineering, and inference workflow.",
                visual_idea="Horizontal flowchart using visual_kit.draw_flowchart showing data stages.",
                key_points=[
                    "Raw telemetry ingestion with automated preprocessing and augmentation.",
                    "Modular feature extraction pipeline with tensor shape validation.",
                    "Downstream task heads with calibrated probability distributions."
                ]
            ),
            PlannedSlide(
                slide_index=3,
                title="Deep Learning Backbone & Subsystem Architecture",
                subtitle="Computational Hierarchy and Tensor Transformations",
                pedagogical_purpose="Teach students how the neural backbone transforms spatial tensors into latent representations.",
                visual_idea="Layer architecture diagram using visual_kit.draw_architecture displaying tensor dimensions.",
                key_points=[
                    "Hierarchical spatial convolutions with residual feature propagation.",
                    "Adaptive pooling layer projecting high-dimensional maps to embeddings.",
                    "Contract-verified method interfaces preventing runtime dimension mismatches."
                ]
            ),
            PlannedSlide(
                slide_index=4,
                title="Empirical Validation & Metric Diagnostics",
                subtitle="Quantitative Performance and Error Analysis",
                pedagogical_purpose="Evaluate classification efficacy, confusion matrix distribution, and baseline comparisons.",
                visual_idea="Confusion matrix or multi-metric comparison chart using visual_kit.",
                key_points=[
                    "High diagnostic sensitivity limits critical clinical false negatives.",
                    "Balanced specificity maintains edge deployment reliability.",
                    "Continuous loss convergence validates optimization stability."
                ]
            ),
            PlannedSlide(
                slide_index=5,
                title="Implementation Contracts & Summary",
                subtitle="Core Method Signatures and Engineering Takeaways",
                pedagogical_purpose="Summarize key software design decisions, unit tests, and student learning outcomes.",
                visual_idea="Three-column milestone subsystem cards using slide_kit.add_card_slide.",
                key_points=[
                    "Modular class separation enables independent testing and verification.",
                    "TDD test harnesses ensure robust edge-case boundary handling.",
                    "Scalable architecture facilitates extension to complex multi-class domains."
                ]
            ),
        ]
        return SlideDeckPlanSchema(
            deck_title=title,
            pedagogical_narrative=f"Comprehensive lesson progression for {title} covering theory, architecture, and evaluation.",
            slides=slides
        )

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
            logger.warning(f"Slide deck planning LLM call encountered error: {e}. Generating default outline.")

        return self._build_default_plan(module, problem_formulation, telemetry)

    def _build_fallback_slide(self, repl: SlideDeckRepl, slide_plan: PlannedSlide):
        """Builds a deterministic slide if LLM code generation fails or adds no slide."""
        prs = repl.prs
        title = slide_plan.title
        subtitle = slide_plan.subtitle or ""
        bullets = slide_plan.key_points or [slide_plan.pedagogical_purpose]
        v_idea = (slide_plan.visual_idea or "").lower()

        try:
            if "flowchart" in v_idea or "pipeline" in v_idea or "stage" in v_idea:
                stages = [
                    {"title": "Input", "desc": "Ingestion & Prep"},
                    {"title": "Backbone", "desc": "Spatial Transforms"},
                    {"title": "Output", "desc": "Prediction & Loss"}
                ]
                img = repl.scope["visual_kit"].draw_flowchart(stages=stages, title=title)
                repl.scope["slide_kit"].add_split_slide(prs, title=title, subtitle=subtitle, left_content=bullets, image_path=img)
            elif "confusion" in v_idea or "matrix" in v_idea or "error" in v_idea:
                matrix = repl.safe_telemetry.get("confusion_matrix") or [[450, 25], [30, 495]]
                img = repl.scope["visual_kit"].draw_confusion_matrix(matrix=matrix, title=title)
                repl.scope["slide_kit"].add_split_slide(prs, title=title, subtitle=subtitle, left_content=bullets, image_path=img)
            elif "metric" in v_idea or "comparison" in v_idea or "benchmark" in v_idea:
                img = repl.scope["visual_kit"].draw_metric_comparison(title=title)
                repl.scope["slide_kit"].add_split_slide(prs, title=title, subtitle=subtitle, left_content=bullets, image_path=img)
            elif "distribution" in v_idea or "balance" in v_idea or "class" in v_idea:
                img = repl.scope["visual_kit"].draw_distribution(labels=["Class A", "Class B"], values=[500, 500], title=title)
                repl.scope["slide_kit"].add_split_slide(prs, title=title, subtitle=subtitle, left_content=bullets, image_path=img)
            elif "code" in v_idea or "signature" in v_idea or "implementation" in v_idea:
                code_snippet = repl.solution_code[:800] if repl.solution_code else "# Module Implementation\ndef execute(): pass"
                repl.scope["slide_kit"].add_code_slide(prs, title=title, subtitle=subtitle, code=code_snippet, notes="\n".join(bullets[:2]))
            else:
                img = repl.scope["visual_kit"].draw_architecture(title=title)
                repl.scope["slide_kit"].add_split_slide(prs, title=title, subtitle=subtitle, left_content=bullets, image_path=img)
        except Exception as e:
            logger.warning(f"Fallback slide construction encountered error: {e}. Adding card slide.")
            cards = [{"title": f"Point {i+1}", "bullets": [b]} for i, b in enumerate(bullets[:3])]
            repl.scope["slide_kit"].add_card_slide(prs, title=title, subtitle=subtitle, cards=cards)

    def generate_presentation_deck(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        solution_code: str,
        telemetry: Dict[str, Any],
        output_path: str,
        max_turns: int = 8
    ) -> Optional[str]:
        """
        Executes an autonomous two-stage presentation design pipeline:
        1. Formulates the broad pedagogical ideas and slide plan.
        2. Iterates slide-by-slide, passing previous slides' context to maintain
           continuity, ensure every planned slide exists, and avoid duplicate slides.
        """
        if not self.client:
            logger.info("No LLM client provided to PresentationDesigner. Skipping presentation generation.")
            return None

        # Stage 1: Formulate the Deck Plan
        logger.info(f"Formulating pedagogical slide deck plan for module '{module.title}'...")
        plan = self._plan_deck(
            module=module,
            problem_formulation=problem_formulation,
            solution_code=solution_code,
            telemetry=telemetry
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            repl = SlideDeckRepl(
                output_path=output_path,
                telemetry=telemetry,
                solution_code=solution_code,
                temp_dir=temp_dir
            )

            completed_slides_log = []

            # Stage 2: Sequential Slide-by-Slide Builder Loop
            for slide_plan in plan.slides:
                idx = slide_plan.slide_index
                logger.info(f"[Slide {idx}/{len(plan.slides)}] Generating: '{slide_plan.title}'...")

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
                        # Self-healing retry turn
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

                # If slide was not added through code, invoke deterministic fallback slide builder
                if not slide_added:
                    logger.info(f"Adding Slide {idx} via deterministic fallback builder.")
                    self._build_fallback_slide(repl, slide_plan)

                completed_slides_log.append(f"- Slide {idx}: '{slide_plan.title}' ({slide_plan.pedagogical_purpose})")

            # Finalize presentation save
            if repl.finalize():
                size = os.path.getsize(output_path)
                logger.info(f"Successfully saved 16:9 presentation deck: {output_path} ({size} bytes, {len(repl.prs.slides)} slides)")
                return output_path
            else:
                logger.warning(f"Presentation deck could not be saved to {output_path}")
                return None
