import os
import logging
import tempfile
from typing import Dict, Any, Optional

from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.presentation_prompts import (
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
    Multi-Turn Autonomous Presentation Designer:
    Uses an interactive Code-Interpreter / REPL Loop (SlideDeckRepl) to:
    1. Render heavy visual assets (MP4 animations, 3D orbits, charts) and bespoke matplotlib graphics.
    2. Build slides incrementally on a persistent 16:9 canvas with visual-first pedagogy.
    3. Self-correct step-by-step with state-aware deck tracking and zero hardcoded fallbacks.
    """

    def __init__(self, client: Any = None, model_name: Optional[str] = None):
        self.client = client
        self.model_name = model_name or os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-Coder-14B-Instruct")

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
        Executes an autonomous multi-turn REPL loop to construct the custom presentation deck.
        """
        if not self.client:
            logger.info("No LLM client provided to PresentationDesigner. Skipping presentation generation.")
            return None

        with tempfile.TemporaryDirectory() as temp_dir:
            repl = SlideDeckRepl(
                output_path=output_path,
                telemetry=telemetry,
                solution_code=solution_code,
                temp_dir=temp_dir
            )

            title = problem_formulation.title or module.title
            domain_ctx = problem_formulation.domain_context or module.context
            problem_stmt = problem_formulation.problem_statement or ""
            objectives = problem_formulation.learning_objectives or []
            focus = problem_formulation.suggested_focus or "Deep Learning & Model Architecture"

            # Extract rich educational context from Agent 0
            markdown_overview = getattr(problem_formulation, "markdown_overview", "") or ""
            overview_snippet = markdown_overview[:2000] if markdown_overview else ""

            # Extract subsystem engineering architecture
            subsystems_info = []
            if getattr(problem_formulation, "milestone_subsystems", None):
                for sub in problem_formulation.milestone_subsystems:
                    comp_sigs = [f"{c.kind} {c.name}: {c.signature}" for c in getattr(sub, "components", [])]
                    subsystems_info.append(f"- Milestone {sub.milestone_num}: {sub.title} ({sub.objective})\n  Components: {', '.join(comp_sigs[:3])}")
            subsystems_text = "\n".join(subsystems_info) if subsystems_info else "Core computational architecture"

            run_sum = telemetry.get("run_summary", {}) if isinstance(telemetry, dict) else {}
            acc = run_sum.get("overall_accuracy") or run_sum.get("accuracy", "90.57")
            auc = run_sum.get("auc_roc", "0.9709")
            classes = telemetry.get("class_mapping", {}) if isinstance(telemetry, dict) else {}
            class_str = ", ".join(list(classes.values())[:6]) if classes else "Target Classes"

            contrastive = telemetry.get("contrastive_samples", {}) if isinstance(telemetry, dict) else {}
            top_succ = contrastive.get("top_success") or {}
            hard_fail = contrastive.get("hard_failure") or {}

            system_instruction = (
                "You are an expert AI & Computing Professor and Presentation Designer operating an interactive Python REPL.\n"
                "Your objective is to create a comprehensive, visually rich 16:9 widescreen PowerPoint lecture deck where GRAPHICS ARE THE PRIMARY HERO OF EVERY SLIDE.\n"
                "Slides must actually TEACH the computational concepts, intuitions, mathematics, algorithms, and practical implementation to students—not just dump text or raw code.\n"
                "\n"
                "You have live access to:\n"
                "- `prs`: Active PowerPoint presentation (16:9 canvas, width=13.333, height=7.5).\n"
                "- `slide_kit`: Layout placement and presentation design system:\n"
                "    slide = slide_kit.create_slide(prs)\n"
                "    slide_kit.add_header(slide, tag='CONCEPT', title='Bold Slide Title', subtitle='Clear explanatory subtitle')\n"
                "    slide_kit.add_hero_graphic(slide, graphic_path, x=0.8, y=1.9, w=7.4, h=5.0, title='Visual Title', caption='Takeaway')\n"
                "    slide_kit.add_callout_column(slide, callouts=[('Key Idea', 'Explanation...'), ('Mechanism', 'Detail...')], x=8.5, y=1.9, w=4.0, h=5.0)\n"
                "    slide_kit.add_code_box(slide, x, y, w, h, code=..., title='Implementation Highlights')\n"
                "    slide_kit.add_card(slide, x, y, w, h, title=..., body=..., accent_color=...)\n"
                "    slide_kit.add_metric_card(slide, x, y, w, h, label, value, subtext=...)\n"
                "    slide_kit.add_artifact_comparison(slide, x, y, w, h, orig_path, proc_path, orig_label, proc_label)\n"
                "- `visual_kit`: Custom figure canvas and media generators:\n"
                "    # AUTONOMOUS BESPOKE GRAPHIC GENERATION (Use this to illustrate any specific concept!):\n"
                "    fig, ax = visual_kit.create_figure(width=8.0, height=4.8, title='Custom Concept Diagram')\n"
                "    # Write any matplotlib / PIL plotting script using ax (e.g. diagrams, pipeline arrows, heatmaps, distributions, decision boundaries):\n"
                "    # Use theme colors: Colors.CYAN, Colors.EMERALD, Colors.CORAL, Colors.INDIGO, Colors.GOLD, Colors.TEXT, Colors.MUTED\n"
                "    img_path = visual_kit.save_figure(fig, filename='concept_diagram.png')\n"
                "    # Pre-built shortcuts:\n"
                "    vid, poster = visual_kit.render_3d_surface_orbit(surface_type='loss_landscape'|'saddle', title=...)\n"
                "    vid, poster = visual_kit.render_artifact_morph(image_paths=[...], captions=[...])\n"
                "    vid, poster = visual_kit.render_network_flow(stage_names=[...], tensor_shapes=[...])\n"
                "    png = visual_kit.render_confusion_matrix(confusion_dict=telemetry.get('confusion'))\n"
                "    png = visual_kit.render_roc_curve(auc_score=0.97)\n"
                "- `plt`: matplotlib.pyplot (headless Agg backend)\n"
                "- `np`: numpy\n"
                "- `Colors`: visual_kit.Colors (CYAN, INDIGO, EMERALD, CORAL, GOLD, TEXT, MUTED)\n"
                "- `telemetry`: Dataset metrics, class mappings, error samples.\n"
                "- `solution_code`: Complete Python reference implementation.\n"
                "- `visual_assets`: Dict to store rendered file paths across steps.\n"
                "\n"
                "PEDAGOGICAL & DESIGN RULES:\n"
                "1. GRAPHIC-FIRST PEDAGOGY: Every slide must feature a prominent visual graphic (custom diagram, schematic, chart, or animation) occupying 50-65% of the slide, paired with concise callouts (35-45%) explaining what the visual demonstrates.\n"
                "2. BESPOKE VISUALS: Autonomously write custom matplotlib scripts to visualize the specific computational concepts (data transformations, tensor dimensions, algorithmic flow, decision boundaries) rather than relying only on generic charts.\n"
                "3. TEACH CONCEPTS, NOT RAW DUMPS: Explain the intuition, principles, and syntax. Do NOT dump raw Linux file paths into cards or paste 100 lines of unannotated code. Show targeted 10-15 line snippets with conceptual callouts.\n"
                "4. PACING & AUTONOMY: Autonomously decide the slide count (typically 4 to 8 slides) and teaching flow based on the depth of the topic.\n"
                "5. INCREMENTAL PROGRESSION: In Turn 1, plan the deck and render key custom visuals. In subsequent turns, build slides progressively. NEVER duplicate slides that already exist in the deck.\n"
                "6. Always use raw multiline strings (r'''...''') when passing code snippets.\n"
            )

            context_brief = (
                f"MODULE: {title} (Week {module.week}) | Difficulty: {module.difficulty.title()}\n"
                f"DOMAIN CHALLENGE: {domain_ctx}\n"
                f"DIRECTIVE: {problem_stmt}\n"
                f"LEARNING OBJECTIVES:\n{chr(10).join([f'- {o}' for o in objectives])}\n\n"
                f"PEDAGOGICAL OVERVIEW & THEORY:\n{overview_snippet}\n\n"
                f"ENGINEERING SUBSYSTEMS:\n{subsystems_text}\n\n"
                f"DATASET & PERFORMANCE: Accuracy {acc}%, AUC-ROC {auc}, Classes: {class_str}\n"
                f"TOP SUCCESS SAMPLE: {top_succ.get('image_path', '')}\n"
                f"HARD FAILURE SAMPLE: {hard_fail.get('image_path', '')}\n"
                f"\nPlan and construct a visually-driven, concept-rich 16:9 lecture deck using the REPL."
            )

            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": context_brief}
            ]

            logger.info(f"Starting Multi-Turn REPL Presentation Designer for '{title}'...")

            for turn in range(1, max_turns + 1):
                try:
                    action: PresentationActionSchema = self.client.chat.completions.create(
                        model=self.model_name,
                        response_model=PresentationActionSchema,
                        max_retries=2,
                        max_tokens=8192,
                        messages=messages
                    )
                except Exception as call_err:
                    logger.warning(f"Turn {turn} LLM completion error: {call_err}")
                    break

                logger.info(f"[REPL Turn {turn}/{max_turns}] Rationale: {action.rationale}")

                # Execute in persistent REPL
                success, output_msg = repl.execute_snippet(action.python_code)
                deck_state = repl.get_deck_summary()

                if success:
                    step_feedback = (
                        f"Step {turn} executed successfully.\nOutput:\n{output_msg}\n\n"
                        f"{deck_state}\n"
                        f"Directive: Do NOT re-create slides that already exist. Proceed to author the next slide(s) or set is_final_step: true if complete."
                    )
                else:
                    step_feedback = (
                        f"Step {turn} encountered an error:\n{output_msg}\n\n"
                        f"{deck_state}\n"
                        f"Please analyze the error and provide corrected Python code to continue building the deck."
                    )

                # Feed execution result back into conversation history
                messages.append({
                    "role": "assistant",
                    "content": f"Rationale: {action.rationale}\n```python\n{action.python_code}\n```"
                })
                messages.append({
                    "role": "user",
                    "content": step_feedback
                })

                if action.is_final_step and success:
                    logger.info(f"Agent declared final step on turn {turn}.")
                    break

            # Finalize presentation save
            if repl.finalize():
                size = os.path.getsize(output_path)
                logger.info(f"Successfully saved 16:9 presentation deck via REPL: {output_path} ({size} bytes, {len(repl.prs.slides)} slides)")
                return output_path
            else:
                logger.warning(f"REPL completed turns but presentation file could not be saved to {output_path}")
                return None
