import os
import sys
import json
import logging
import tempfile
import subprocess
import traceback
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from digitalagedu.core.llm import slide_kit
from digitalagedu.core.llm.visuals import visual_kit
from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema

logger = logging.getLogger(__name__)

# Execution timeout: 3 minutes (180 seconds)
SUBPROCESS_TIMEOUT_SECONDS = 180


class PresentationCodeSchema(BaseModel):
    """Schema for LLM-synthesized Python presentation generation script."""
    design_rationale: str = Field(
        ...,
        description="High-level pedagogical and visual layout rationale for the slides."
    )
    python_code: str = Field(
        ...,
        description="Complete, valid Python script defining `def build_presentation(prs, slide_kit, visual_kit, telemetry, solution_code):` using python-pptx, slide_kit, and visual_kit."
    )


def build_presentation_designer_prompt(
    module: Module,
    problem_formulation: ProblemStatementSchema,
    solution_code: str,
    telemetry: Dict[str, Any]
) -> str:
    """Builds the comprehensive instruction prompt for the LLM Presentation Designer."""
    title = problem_formulation.title or module.title
    domain_ctx = problem_formulation.domain_context or module.context
    problem_stmt = problem_formulation.problem_statement or ""
    objectives = problem_formulation.learning_objectives or []
    target_in = problem_formulation.target_input_shape or "[Batch, Channels, Height, Width]"
    target_out = problem_formulation.target_output_shape or "[Batch, NumClasses]"
    focus = problem_formulation.suggested_focus or "Deep Learning & Model Architecture"

    run_sum = telemetry.get("run_summary", {}) if isinstance(telemetry, dict) else {}
    acc = run_sum.get("overall_accuracy") or run_sum.get("accuracy", "90.57")
    auc = run_sum.get("auc_roc", "0.9709")
    samples = run_sum.get("total_images") or run_sum.get("total_samples", "3297")
    classes = telemetry.get("class_mapping", {}) if isinstance(telemetry, dict) else {}
    class_str = ", ".join(list(classes.values())[:6]) if classes else "Target Classes"

    contrastive = telemetry.get("contrastive_samples", {}) if isinstance(telemetry, dict) else {}
    top_succ = contrastive.get("top_success") or {}
    hard_fail = contrastive.get("hard_failure") or {}

    prompt = f"""You are an expert AI Presentation Designer and Applied Deep Learning Educator.
Your task is to write a clean, creative Python function `build_presentation(prs, slide_kit, visual_kit, telemetry, solution_code)` that creates a comprehensive, visually rich 16:9 widescreen PowerPoint lecture deck.

--- SLIDE COUNT & PACING AUTONOMY ---
You have full creative freedom to decide how many slides to generate based on the topic's depth (typically between 4 to 8 slides). Pacing matters: break complex concepts across multiple focused slides rather than overcrowding a single slide.
Do NOT stick to rigid templates. Combine media, code, metrics, and text dynamically on the 16:9 canvas (Width 13.333", Height 7.5").

--- MODULE CONTEXT & TELEMETRY ---
Module: {module.title} (Week {module.week}) | Difficulty: {module.difficulty.title()}
Domain Application: {domain_ctx}
Core Problem Directive: {problem_stmt}
Focus Area: {focus}
Tensor Shape Contracts: Input `{target_in}` ➔ Output `{target_out}`
Learning Objectives:
{chr(10).join([f"- {obj}" for obj in objectives])}

Pipeline Telemetry:
- Total Dataset Samples: {samples}
- Phase 1 Baseline Accuracy: {acc}% | AUC-ROC: {auc}
- Dataset Classes: {class_str}
- Top Success Case: {top_succ.get('image_path', 'sample.jpg')} (True: {top_succ.get('ground_truth', 'Target')})
- Hard Failure Case: {hard_fail.get('image_path', 'failure.jpg')} (True: {hard_fail.get('ground_truth')}, Predicted: {hard_fail.get('predicted_class')})

Reference Solution Code:
```python
{solution_code}
```

--- TWO-TIER VISUAL TOOLKIT ---

TIER 1: Visual Asset Producers (`visual_kit`)
Generates rich media files (.mp4 or .png) saved to disk that you embed into slides:
- `video_path, poster_path = visual_kit.render_artifact_morph(image_paths=[...], captions=[...])`
  Creates a cross-dissolve video transition between 2+ authentic pipeline images (Raw -> Mask -> Grad-CAM).
- `video_path, poster_path = visual_kit.render_3d_surface_orbit(surface_type='loss_landscape'|'saddle', title=...)`
  Creates a rotating 3D camera orbit around an optimization surface or saddle manifold.
- `video_path, poster_path = visual_kit.render_3d_scatter_orbit(points_3d=None, labels=None, title=...)`
  Creates a rotating 3D camera orbit around latent embedding clusters (PCA/t-SNE).
- `video_path, poster_path = visual_kit.render_network_flow(stage_names=[...], tensor_shapes=[...], title=...)`
  Creates an animated forward-pass progression across architecture layers.
- `video_path, poster_path = visual_kit.render_attention_matrix_animation(matrix=None, tokens=[...], title=...)`
  Creates an animated heatmap pulse of self-attention weights.
- `png_path = visual_kit.render_confusion_matrix(confusion_dict=telemetry.get('confusion'), title=...)`
  Renders a confusion matrix chart from telemetry.
- `png_path = visual_kit.render_class_distribution(class_counts=telemetry.get('class_distribution'), title=...)`
  Renders a dataset class balance bar chart.
- `png_path = visual_kit.render_roc_curve(auc_score=0.97, title=...)`
  Renders an ROC-AUC diagnostic curve.

TIER 2: Slide Canvas Placement (`slide_kit`)
Positions shapes and media freely at any (x, y, w, h) coordinates:
- `slide_kit.Theme`: `BG_DARK`, `BG_LIGHT`, `CARD_BG`, `CARD_BORDER`, `TEXT_PRIMARY`, `TEXT_MUTED`, `ACCENT_CYAN`, `ACCENT_INDIGO`, `ACCENT_EMERALD`, `ACCENT_CORAL`, `ACCENT_GOLD`, `CODE_BG`, `CODE_TEXT`.
- `slide = slide_kit.create_slide(prs, bg_color=None)`: Creates a 16:9 slide (Width 13.333", Height 7.5").
- `slide_kit.add_header(slide, tag, title, subtitle=None, tag_color=None)`: Adds category pill and bold title.
- `slide_kit.add_video(slide, x, y, w, h, video_path, poster_image_path=None)`: Embeds an MP4 video with poster frame preview.
- `slide_kit.add_image(slide, x, y, w, h, image_path, caption=None)`: Embeds an image or chart with optional caption.
- `slide_kit.add_artifact_comparison(slide, x, y, w, h, original_path, processed_path, original_label, processed_label)`: Side-by-side artifact comparison.
- `slide_kit.add_code_box(slide, x, y, w, h, code, title=None)`: Dark IDE code block.
- `slide_kit.add_card(slide, x, y, w, h, title=None, body=None, accent_color=None)`: Container card.
- `slide_kit.add_metric_card(slide, x, y, w, h, label, value, subtext=None, accent_color=None)`: KPI stat card.
- `slide_kit.add_callout_banner(slide, x, y, w, h, text, title='KEY TAKEAWAY', accent_color=None)`: Takeaway banner.

--- CRITICAL CODE RULES ---
1. Define a top-level function:
   `def build_presentation(prs, slide_kit, visual_kit, telemetry, solution_code):`
2. Allowed imports at the top:
   ```python
   import pptx
   from pptx.util import Inches, Pt
   from pptx.dml.color import RGBColor
   import slide_kit
   from slide_kit import Theme
   import visual_kit
   ```
3. Use the passed `prs` object (do NOT instantiate `Presentation()`).
4. Ensure all coordinates fit within the 16:9 canvas (Width: 13.333 inches, Height: 7.5 inches).
5. Code MUST be valid, self-contained Python without markdown backticks.
"""
    return prompt


class SafeTelemetryDict(dict):
    """Typo-tolerant dictionary wrapper for telemetry."""
    def __init__(self, data=None):
        super().__init__()
        if data and isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, dict):
                    self[k] = SafeTelemetryDict(v)
                elif isinstance(v, list):
                    self[k] = [SafeTelemetryDict(item) if isinstance(item, dict) else item for item in v]
                else:
                    self[k] = v

    def __getitem__(self, key):
        if not isinstance(key, str):
            return super().get(key, SafeTelemetryDict())
        if key in self:
            return super().__getitem__(key)
        for k, v in self.items():
            if isinstance(k, str) and k.lower() == key.lower():
                return v
        return SafeTelemetryDict()

    def get(self, key, default=None):
        try:
            val = self[key]
            if isinstance(val, SafeTelemetryDict) and len(val) == 0:
                return default
            return val
        except Exception:
            return default

    def __getattr__(self, name):
        return self[name]


class PresentationActionSchema(BaseModel):
    """Schema for individual REPL actions executed during multi-turn slide generation."""
    rationale: str = Field(
        ...,
        description="Clear engineering explanation of this turn's actions."
    )
    python_code: str = Field(
        ...,
        description="Python code to execute against the active presentation environment."
    )
    is_final_step: bool = Field(
        default=False,
        description="Set to True when all slides are constructed and prs.save() should finalize the deck."
    )


class SlideDeckRepl:
    """
    Stateful Interactive REPL sandbox for incremental slide and visual asset construction.
    Maintains active pptx.Presentation, slide_kit, visual_kit, and telemetry state across turns.
    """

    def __init__(
        self,
        output_path: str,
        telemetry: Dict[str, Any],
        solution_code: str,
        temp_dir: str
    ):
        self.output_path = output_path
        self.telemetry = telemetry
        self.solution_code = solution_code
        self.temp_dir = temp_dir
        self.history: List[str] = []

        # Local execution namespace
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor

        self.prs = Presentation()
        self.prs.slide_width = Inches(slide_kit.SLIDE_WIDTH_INCHES)
        self.prs.slide_height = Inches(slide_kit.SLIDE_HEIGHT_INCHES)

        assets_dir = os.path.join(os.path.dirname(os.path.abspath(output_path)), "presentation_assets")
        os.makedirs(assets_dir, exist_ok=True)
        visual_kit.output_dir = assets_dir

        self.safe_telemetry = SafeTelemetryDict(telemetry)
        self.visual_assets: Dict[str, Any] = {}

        # Register in sys.modules so 'import slide_kit' and 'import visual_kit' work directly
        sys.modules["slide_kit"] = slide_kit
        sys.modules["visual_kit"] = visual_kit

        # Initial namespace binding
        self.scope = {
            "os": os,
            "sys": sys,
            "json": json,
            "pptx": __import__("pptx"),
            "Presentation": Presentation,
            "Inches": Inches,
            "Pt": Pt,
            "RGBColor": RGBColor,
            "slide_kit": slide_kit,
            "Theme": slide_kit.Theme,
            "visual_kit": visual_kit,
            "prs": self.prs,
            "telemetry": self.safe_telemetry,
            "solution_code": self.solution_code,
            "visual_assets": self.visual_assets,
            "slides": [],
        }

    def execute_snippet(self, code_snippet: str) -> Tuple[bool, str]:
        """
        Executes a Python code chunk within the persistent presentation scope.
        Returns (success: bool, output_or_error_message: str).
        """
        cleaned = code_snippet.strip()
        if cleaned.startswith("```python"):
            cleaned = cleaned[len("```python"):].strip()
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:].strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()

        # Capture stdout & stderr
        import io
        from contextlib import redirect_stdout, redirect_stderr

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()

        try:
            with redirect_stdout(stdout_buf), redirect_stderr(stderr_buf):
                exec(cleaned, self.scope)
            self.history.append(cleaned)
            out_str = stdout_buf.getvalue().strip()
            err_str = stderr_buf.getvalue().strip()
            combined = f"{out_str}\n{err_str}".strip() if err_str else (out_str or "Success: Step executed cleanly.")
            return True, combined
        except Exception as e:
            tb = traceback.format_exc()
            return False, f"Execution Error: {e}\n{tb}"

    def finalize(self) -> bool:
        """Saves the presentation to the target output path."""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.output_path)), exist_ok=True)
            self.prs.save(self.output_path)
            return os.path.exists(self.output_path) and os.path.getsize(self.output_path) > 0
        except Exception as e:
            logger.error(f"Failed to save final presentation deck: {e}")
            return False


def execute_presentation_code_sandbox(
    python_code: str,
    output_path: str,
    telemetry: Optional[Dict[str, Any]] = None,
    solution_code: str = "",
    timeout: int = SUBPROCESS_TIMEOUT_SECONDS
) -> Tuple[bool, str]:
    """
    Backwards-compatible execution sandbox using SlideDeckRepl.
    Executes a script and calls build_presentation(prs, slide_kit, visual_kit, telemetry, solution_code) if defined.
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            repl = SlideDeckRepl(
                output_path=output_path,
                telemetry=telemetry or {},
                solution_code=solution_code,
                temp_dir=temp_dir
            )
            ok, msg = repl.execute_snippet(python_code)
            if not ok:
                return False, msg

            if "build_presentation" in repl.scope and callable(repl.scope["build_presentation"]):
                try:
                    repl.scope["build_presentation"](
                        prs=repl.prs,
                        slide_kit=repl.scope["slide_kit"],
                        visual_kit=repl.scope["visual_kit"],
                        telemetry=repl.safe_telemetry,
                        solution_code=repl.solution_code
                    )
                except Exception as call_e:
                    return False, f"build_presentation error: {call_e}\n{traceback.format_exc()}"

            saved = repl.finalize()
            if not saved:
                return False, "Failed to save generated presentation to disk."
            return True, f"Successfully created presentation: {output_path}"
    except Exception as e:
        return False, f"Sandbox error: {e}\n{traceback.format_exc()}"


class PresentationDesigner:
    """
    Multi-Turn Autonomous Presentation Designer:
    Uses an interactive Code-Interpreter / REPL Loop (SlideDeckRepl) to:
    1. Render heavy visual assets (MP4 animations, 3D orbits, charts) first.
    2. Build slides incrementally on a persistent 16:9 canvas.
    3. Self-correct step-by-step with zero hardcoded template fallbacks.
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

            run_sum = telemetry.get("run_summary", {}) if isinstance(telemetry, dict) else {}
            acc = run_sum.get("overall_accuracy") or run_sum.get("accuracy", "90.57")
            auc = run_sum.get("auc_roc", "0.9709")
            classes = telemetry.get("class_mapping", {}) if isinstance(telemetry, dict) else {}
            class_str = ", ".join(list(classes.values())[:6]) if classes else "Target Classes"

            contrastive = telemetry.get("contrastive_samples", {}) if isinstance(telemetry, dict) else {}
            top_succ = contrastive.get("top_success") or {}
            hard_fail = contrastive.get("hard_failure") or {}

            system_instruction = (
                "You are an expert AI Presentation Designer operating an interactive Python REPL.\n"
                "You have live access to:\n"
                "- `prs`: Active PowerPoint presentation (16:9 canvas, width=13.333, height=7.5).\n"
                "- `slide_kit`: High-level layout placement functions:\n"
                "    slide = slide_kit.create_slide(prs)\n"
                "    slide_kit.add_header(slide, tag, title, subtitle=None)\n"
                "    slide_kit.add_card(slide, x, y, w, h, title=..., body=..., accent_color=...)\n"
                "    slide_kit.add_metric_card(slide, x, y, w, h, label, value, subtext=...)\n"
                "    slide_kit.add_code_box(slide, x, y, w, h, code=..., title=...)\n"
                "    slide_kit.add_video(slide, x, y, w, h, video_path, poster_image_path=None)\n"
                "    slide_kit.add_image(slide, x, y, w, h, image_path, caption=...)\n"
                "    slide_kit.add_artifact_comparison(slide, x, y, w, h, orig_path, proc_path, orig_label, proc_label)\n"
                "    slide_kit.add_callout_banner(slide, x, y, w, h, text=..., title=...)\n"
                "- `visual_kit`: Media generators saved to disk:\n"
                "    vid, poster = visual_kit.render_3d_surface_orbit(surface_type='loss_landscape'|'saddle', title=...)\n"
                "    vid, poster = visual_kit.render_artifact_morph(image_paths=[...], captions=[...])\n"
                "    vid, poster = visual_kit.render_network_flow(stage_names=[...], tensor_shapes=[...])\n"
                "    png = visual_kit.render_confusion_matrix(confusion_dict=telemetry.get('confusion'))\n"
                "    png = visual_kit.render_roc_curve(auc_score=0.97)\n"
                "- `telemetry`: Dataset metrics, class mappings, and results.\n"
                "- `solution_code`: Complete Python reference implementation.\n"
                "- `visual_assets`: Dict to store rendered file paths across steps.\n"
                "\n"
                "OPERATIONAL GUIDELINES:\n"
                "1. TURN 1: Call `visual_kit` to render 1-2 key visual animations (3D orbit, ROC curve, or confusion matrix) and store paths in `visual_assets`.\n"
                "2. SUBSEQUENT TURNS: Construct slides 1-by-1 or 2-by-2 using `slide_kit`. Embed generated visuals and code boxes.\n"
                "3. FINAL TURN: Set `is_final_step: true` when all 4 to 8 slides are built.\n"
                "4. Always use raw multiline strings (r'''...''') when passing code snippets to prevent escape sequence syntax errors.\n"
            )

            context_brief = (
                f"MODULE: {title} (Week {module.week})\n"
                f"DOMAIN: {domain_ctx}\n"
                f"OBJECTIVES: {', '.join(objectives[:3])}\n"
                f"DATASET: Accuracy {acc}%, AUC-ROC {auc}, Classes: {class_str}\n"
                f"TOP SUCCESS SAMPLE: {top_succ.get('image_path', '')}\n"
                f"HARD FAILURE SAMPLE: {hard_fail.get('image_path', '')}\n"
                f"\nPlan and build a complete 4-8 slide 16:9 widescreen presentation deck using the REPL."
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

                if success:
                    step_feedback = f"Step {turn} executed successfully.\nOutput:\n{output_msg}"
                else:
                    step_feedback = (
                        f"Step {turn} encountered an error:\n{output_msg}\n"
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

