from typing import Dict, Any
from pydantic import BaseModel, Field

from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema

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
- `img_path = visual_kit.draw_flowchart(steps=[('Step 1', 'Detail'), ...], title=...)`
  Draws an aesthetic process flowchart with step cards and directional arrows.
- `img_path = visual_kit.draw_architecture(layers=[{'name': 'Input', 'detail': '(B, 3, 224, 224)'}, ...], title=...)`
  Draws a neural network / subsystem architecture diagram with tensor dimension pills and flow arrows.
- `img_path = visual_kit.draw_confusion_matrix(matrix=telemetry.get('confusion'), class_names=[...], title=...)`
  Safely renders a normalized confusion matrix heatmap with high-contrast cell counts and percentages.
- `img_path = visual_kit.draw_metric_comparison(metrics={'Accuracy': 92.4, 'AUC-ROC': 97.1}, title=...)`
  Renders a modern, high-contrast horizontal benchmark bar comparison chart.
- `img_path = visual_kit.draw_distribution(class_counts={'Class A': 500, 'Class B': 500}, title=...)`
  Renders a class distribution chart with bright, high-contrast text labels.
- `fig, ax = visual_kit.create_figure(width=8.0, height=4.8, title=...)`
  Creates a themed matplotlib canvas for bespoke concept diagrams and flows.
- `img_path = visual_kit.save_figure(fig, filename=...)`
  Saves the custom matplotlib figure and returns the image path.
- `video_path, poster_path = visual_kit.render_artifact_morph(image_paths=[...], captions=[...])`
  Creates a cross-dissolve video transition between 2+ authentic pipeline images.
- `video_path, poster_path = visual_kit.render_3d_surface_orbit(surface_type='loss_landscape'|'saddle', title=...)`
  Creates a rotating 3D camera orbit around an optimization surface or saddle manifold.
- `video_path, poster_path = visual_kit.render_3d_scatter_orbit(points_3d=None, labels=None, title=...)`
  Creates a rotating 3D camera orbit around latent embedding clusters (PCA/t-SNE).
- `video_path, poster_path = visual_kit.render_network_flow(stage_names=[...], tensor_shapes=[...], title=...)`
  Creates an animated forward-pass progression across architecture layers.

TIER 2: Slide Canvas Placement (`slide_kit`)
Positions shapes and media freely on the 16:9 canvas (Width 13.333", Height 7.5"):
- `slide = slide_kit.create_slide(prs)`
- `slide_kit.add_header(slide, tag, title, subtitle=None)`
- `slide_kit.add_hero_graphic(slide, graphic_path, x, y, w, h, title=..., caption=...)`
- `slide_kit.add_callout_column(slide, callouts=[...], x, y, w, h)`
- `slide_kit.add_code_box(slide, x, y, w, h, code, title=None)`
- `slide_kit.add_card(slide, x, y, w, h, title=None, body=None, accent_color=None)`
- `slide_kit.add_metric_card(slide, x, y, w, h, label, value, subtext=None)`
- `slide_kit.add_artifact_comparison(slide, x, y, w, h, orig_path, proc_path, orig_label, proc_label)`
"""
    return prompt

