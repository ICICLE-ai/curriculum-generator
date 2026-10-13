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


def execute_presentation_code_sandbox(
    python_code: str,
    output_path: str,
    telemetry: Dict[str, Any],
    solution_code: str,
    timeout: int = SUBPROCESS_TIMEOUT_SECONDS
) -> Tuple[bool, Optional[str]]:
    """
    Executes the LLM-generated presentation script in an isolated subprocess sandbox.
    Has a strict 3-minute timeout to allow rich media rendering.
    Returns (success, log_or_error_message).
    """
    cleaned_code = python_code.strip()
    if cleaned_code.startswith("```python"):
        cleaned_code = cleaned_code[len("```python"):].strip()
    elif cleaned_code.startswith("```"):
        cleaned_code = cleaned_code[3:].strip()
    if cleaned_code.endswith("```"):
        cleaned_code = cleaned_code[:-3].strip()

    with tempfile.TemporaryDirectory() as temp_dir:
        # Write telemetry and solution fixtures
        telemetry_file = os.path.join(temp_dir, "telemetry.json")
        with open(telemetry_file, "w", encoding="utf-8") as f:
            json.dump(telemetry, f)

        solution_file = os.path.join(temp_dir, "solution.py")
        with open(solution_file, "w", encoding="utf-8") as f:
            f.write(solution_code)

        # Write user-generated script
        user_script = os.path.join(temp_dir, "user_presentation.py")
        with open(user_script, "w", encoding="utf-8") as f:
            f.write(cleaned_code)

        # Write orchestrating runner
        runner_content = f"""import os
import sys
import json
from pptx import Presentation
from pptx.util import Inches

from digitalagedu.core.llm import slide_kit
from digitalagedu.core.llm.visuals import visual_kit
from digitalagedu.core.llm.presentation_designer import SafeTelemetryDict

sys.modules["slide_kit"] = slide_kit
sys.modules["visual_kit"] = visual_kit

with open(r"{telemetry_file}", "r", encoding="utf-8") as f:
    raw_telemetry = json.load(f)
safe_telemetry = SafeTelemetryDict(raw_telemetry)

with open(r"{solution_file}", "r", encoding="utf-8") as f:
    sol_code = f.read()

import user_presentation

prs = Presentation()
prs.slide_width = Inches(slide_kit.SLIDE_WIDTH_INCHES)
prs.slide_height = Inches(slide_kit.SLIDE_HEIGHT_INCHES)

build_fn = getattr(user_presentation, "build_presentation", None)
if not build_fn or not callable(build_fn):
    print("ERROR: Generated code did not define a callable `build_presentation` function.", file=sys.stderr)
    sys.exit(1)

# Check function argument count to support both 4 and 5 parameter signatures
import inspect
sig = inspect.signature(build_fn)
n_params = len(sig.parameters)

if n_params >= 5:
    build_fn(prs, slide_kit, visual_kit, safe_telemetry, sol_code)
else:
    build_fn(prs, slide_kit, safe_telemetry, sol_code)

out_file = r"{output_path}"
os.makedirs(os.path.dirname(os.path.abspath(out_file)), exist_ok=True)
prs.save(out_file)
print("SUCCESS")
"""
        runner_file = os.path.join(temp_dir, "run_deck.py")
        with open(runner_file, "w", encoding="utf-8") as f:
            f.write(runner_content)

        env = os.environ.copy()
        pkg_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        pythonpath_entries = [
            pkg_root,
            "/app",
            os.path.abspath("."),
            temp_dir,
            env.get("PYTHONPATH", "")
        ]
        env["PYTHONPATH"] = os.pathsep.join([p for p in pythonpath_entries if p])

        try:
            res = subprocess.run(
                [sys.executable, runner_file],
                cwd=temp_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout
            )
            if res.returncode == 0 and os.path.exists(output_path):
                return True, res.stdout
            err_msg = res.stderr or res.stdout or f"Process returned non-zero code {res.returncode}"
            return False, err_msg
        except subprocess.TimeoutExpired:
            return False, f"Presentation script execution timed out after {timeout} seconds."
        except Exception as e:
            return False, f"Subprocess execution exception: {str(e)}\n{traceback.format_exc()}"


class PresentationDesigner:
    """
    Agentic Presentation Designer:
    Synthesizes custom 16:9 PowerPoint code using slide_kit and visual_kit,
    verifies execution in a 3-minute isolated subprocess sandbox, and self-heals errors.
    Non-fatal if generation fails (does not crash the broader pipeline).
    """

    def __init__(self, client: Any = None, model_name: Optional[str] = None):
        self.client = client
        self.model_name = model_name or os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ")

    def generate_presentation_deck(
        self,
        module: Module,
        problem_formulation: ProblemStatementSchema,
        solution_code: str,
        telemetry: Dict[str, Any],
        output_path: str
    ) -> Optional[str]:
        """
        Generates and executes a custom 16:9 presentation deck via LLM code synthesis with self-healing.
        Returns the output file path on success, or None on failure (non-fatal).
        """
        if not self.client:
            logger.info("No LLM client provided to PresentationDesigner. Skipping presentation generation.")
            return None

        designer_prompt = build_presentation_designer_prompt(
            module=module,
            problem_formulation=problem_formulation,
            solution_code=solution_code,
            telemetry=telemetry
        )

        logger.info(f"Synthesizing custom 16:9 presentation code with {self.model_name}...")
        try:
            res: PresentationCodeSchema = self.client.chat.completions.create(
                model=self.model_name,
                response_model=PresentationCodeSchema,
                max_retries=2,
                max_tokens=16384,
                messages=[
                    {"role": "system", "content": "You are a master presentation designer and senior Python programmer."},
                    {"role": "user", "content": designer_prompt}
                ]
            )

            success, err = execute_presentation_code_sandbox(
                python_code=res.python_code,
                output_path=output_path,
                telemetry=telemetry,
                solution_code=solution_code,
                timeout=SUBPROCESS_TIMEOUT_SECONDS
            )

            if not success:
                logger.warning(f"Presentation execution failed on initial attempt: {err}. Triggering self-healing retry...")
                retry_prompt = f"{designer_prompt}\n\n--- PREVIOUS EXECUTION ERROR ---\n{err}\n\nPlease fix the python_code to resolve the error."
                
                retry_res: PresentationCodeSchema = self.client.chat.completions.create(
                    model=self.model_name,
                    response_model=PresentationCodeSchema,
                    max_retries=2,
                    max_tokens=16384,
                    messages=[
                        {"role": "system", "content": "You are a master presentation designer and senior Python programmer."},
                        {"role": "user", "content": retry_prompt}
                    ]
                )
                success, err = execute_presentation_code_sandbox(
                    python_code=retry_res.python_code,
                    output_path=output_path,
                    telemetry=telemetry,
                    solution_code=solution_code,
                    timeout=SUBPROCESS_TIMEOUT_SECONDS
                )
                if not success:
                    logger.warning(f"Presentation execution failed after retry: {err}. Skipping presentation generation.")
                    return None

            if os.path.exists(output_path):
                logger.info(f"Successfully saved 16:9 presentation deck: {output_path} ({os.path.getsize(output_path)} bytes)")
                return output_path
            return None

        except Exception as e:
            logger.warning(f"Presentation generation hit exception: {e}. Skipping deck build.")
            return None
