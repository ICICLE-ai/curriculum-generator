from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema

SUBPROCESS_TIMEOUT_SECONDS = 180


class ConceptVisualSpec(BaseModel):
    """Specification of the visual graphic or animation for a single core concept."""
    category: Literal[
        "flowchart",
        "network_architecture",
        "confusion_matrix",
        "metric_comparison",
        "data_distribution",
        "loss_surface_3d",
        "artifact_morph",
        "custom_matplotlib"
    ] = Field(
        ...,
        description="The primary category of visual generator in visual_kit to use."
    )
    visual_idea: str = Field(
        ...,
        description="Detailed visual specification (e.g. 'draw_architecture with input (B, 3, 224, 224) -> ViT -> Class logits')."
    )
    suggested_recipe_query: str = Field(
        ...,
        description="Search keywords to retrieve matching atomic visual recipe from Qdrant vector database."
    )
    use_artifact: bool = Field(
        default=False,
        description="Whether to incorporate authentic pipeline image/mask artifacts into this visual."
    )
    artifact_type: Optional[str] = Field(
        default=None,
        description="Optional artifact role: 'raw_sample', 'mask_sample', 'contrastive_pair', or None."
    )


class DiscretizedConcept(BaseModel):
    """A single, discrete core concept within a curriculum module."""
    concept_index: int = Field(..., ge=1, le=5, description="1-indexed concept number (1 to 5).")
    title: str = Field(..., description="Concise, concept-focused title (e.g. 'Spatial ViT Patch Embedding Alignment').")
    algorithmic_principle: str = Field(
        ...,
        description="Core mathematical or algorithmic concept being taught (e.g. self-supervised patch projection, IoU calculation)."
    )
    domain_application: str = Field(
        ...,
        description="Direct connection to real-world domain problem (e.g. identifying necrotic lesions, foliar pathology, dermatoscopy)."
    )
    pipeline_data_flow: str = Field(
        ...,
        description="Data flow, tensor dimensions, or mathematical transformations (e.g. [B, 3, 224, 224] -> [B, 196, 768])."
    )
    key_takeaways: List[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="2 to 4 high-impact technical takeaways explaining the principle and engineering intuition."
    )
    visual_spec: ConceptVisualSpec = Field(
        ...,
        description="Visual specification and generator assignment for this concept."
    )


class DiscretizedConceptPlan(BaseModel):
    """Concept architecture plan distilling a module into 3 to 5 discrete, non-overlapping concepts."""
    deck_title: str = Field(..., description="High-level presentation title.")
    domain_subtitle: str = Field(..., description="Domain problem and clinical/physical motivation subtitle.")
    pedagogical_narrative: str = Field(
        ...,
        description="Overall narrative arc guiding students from domain problem through algorithmic mechanics to empirical validation."
    )
    concepts: List[DiscretizedConcept] = Field(
        ...,
        min_length=3,
        max_length=5,
        description="Exactly 3 to 5 discrete, mutually exclusive core concepts. No concept may repeat or bleed into another."
    )
    synthesis_takeaways: List[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="2 to 4 overarching synthesis points for the final summary slide."
    )


class PlannedSlide(BaseModel):
    """Architectural plan for a single slide in the lecture deck."""
    slide_index: int = Field(..., description="1-indexed position of this slide in the lecture deck.")
    title: str = Field(..., description="Clear, concept-driven slide title.")
    subtitle: Optional[str] = Field(default="", description="Subtitle summarizing the key idea.")
    pedagogical_purpose: str = Field(
        ...,
        description="What concept, algorithm, intuition, or empirical result this slide teaches students."
    )
    visual_idea: str = Field(
        ...,
        description="Detailed specification of what visual graphic, chart, architecture diagram, flowchart, or plot to render."
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Explanatory callouts, mathematical formulas, or architectural takeaways to pair with the visual."
    )


class SlideDeckPlanSchema(BaseModel):
    """Comprehensive architectural plan for the entire lecture presentation."""
    deck_title: str = Field(..., description="High-level title for this lecture deck.")
    pedagogical_narrative: str = Field(
        ...,
        description="The conceptual journey of the lesson (from intuition/problem formulation to methodology, implementation, and evaluation)."
    )
    slides: List[PlannedSlide] = Field(
        ...,
        description="The planned sequence of slides. The planner autonomously determines the optimal slide count and depth based on topic complexity."
    )


class SingleSlideCodeSchema(BaseModel):
    """Executable Python snippet for building one planned slide."""
    rationale: str = Field(
        ...,
        description="Explanation of how this slide is rendered and aligned with the planned objective."
    )
    python_code: str = Field(
        ...,
        description="Executable Python snippet using slide_kit, visual_kit, and/or matplotlib that renders the graphic and adds EXACTLY ONE slide to `prs`."
    )


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


CONCEPT_DISCRETIZER_SYSTEM = """You are an expert AI & Computing Professor and Curriculum Architect.
Your role is to analyze a deep learning/computing module and discretize it into EXACTLY 3 TO 5 CORE CONCEPTS.

STRICT PEDAGOGICAL INVARIANTS:
1. MUTUALLY EXCLUSIVE CONCEPTS (NO BLEEDING):
   Each concept must address a distinct, self-contained algorithmic or theoretical milestone.
   Never create duplicate concepts, repeated overview slides, or fragmented sub-steps.
   For example, do NOT create multiple slides on 'Random Forest Growth' or multiple 'Introduction' slides.
2. DOMAIN-GROUNDED COMPUTING:
   Anchor every concept in the physical/domain problem (e.g. agricultural foliar pathology, dermatoscopy, disaster response).
   Explain *why* this computational technique is necessary to solve that real-world challenge.
3. VISUAL SPECIFICATION & ARTIFACT INTEGRATION:
   Every concept must feature a dedicated visual medium.
   When authentic pipeline artifacts (raw images, masks, contrastive samples) are available and relevant, designate their usage in `visual_spec`.
4. COUNT BOUNDS:
   You MUST return between 3 and 5 concepts in `concepts`. Never return fewer than 3 or more than 5.
"""


def build_concept_discretizer_prompt(
    module: Module,
    problem_formulation: ProblemStatementSchema,
    solution_code: str,
    telemetry: Dict[str, Any],
    artifacts: Optional[Dict[str, str]] = None
) -> str:
    """Constructs prompt for Agent A (Concept Discretizer)."""
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

    # Summarize milestone subsystems
    subsystems_info = []
    if getattr(problem_formulation, "milestone_subsystems", None):
        for sub in problem_formulation.milestone_subsystems:
            comp_sigs = [f"{c.kind} {c.name}: {c.signature}" for c in getattr(sub, "components", [])]
            subsystems_info.append(f"- Milestone {sub.milestone_num}: {sub.title} ({sub.objective}) -> Components: {', '.join(comp_sigs[:2])}")
    subsystems_text = "\n".join(subsystems_info) if subsystems_info else "Core computational pipeline"

    # Artifact inventory
    artifact_lines = []
    if artifacts:
        for k, v in artifacts.items():
            if v:
                artifact_lines.append(f"- `{k}`: {v}")
    artifact_str = "\n".join(artifact_lines) if artifact_lines else "- No local sample image fixtures registered."

    # Reference solution snippet
    sol_lines = [l for l in solution_code.strip().split("\n") if not l.startswith('"""') and not l.startswith("'''")]
    compact_solution = "\n".join(sol_lines[:45])

    return f"""MODULE: {title} (Week {module.week}) | Difficulty: {module.difficulty.title()}
DOMAIN APPLICATION: {domain_ctx}
CORE PROBLEM DIRECTIVE: {problem_stmt}
PEDAGOGICAL FOCUS: {focus}

LEARNING OBJECTIVES:
{chr(10).join([f"- {o}" for o in objectives])}

PIPELINE & SUBSYSTEM ARCHITECTURE:
{subsystems_text}

VERIFIED REFERENCE SOLUTION (ALGORITHMIC CONTRACT):
```python
{compact_solution}
```

PIPELINE TELEMETRY:
- Baseline Accuracy: {acc}% | AUC-ROC: {auc}
- Target Classes: {class_str}

AVAILABLE AUTHENTIC PIPELINE ARTIFACTS:
{artifact_str}

DIRECTIVE:
Analyze this module, its domain application, and its reference code.
Distill the module into exactly 3 to 5 discrete, foundational concepts.
Each concept must be distinct and non-overlapping.
Assign an exact visual specification to each concept, indicating where authentic pipeline artifacts should be incorporated."""


CONCEPT_SLIDE_BUILDER_SYSTEM = """You are an expert Presentation Designer and Python Developer.
You construct individual PowerPoint lecture slides in a stateful Python REPL using `slide_kit` and `visual_kit`.

CRITICAL INVARIANTS:
1. EXACTLY ONE SLIDE: Your code must add EXACTLY ONE slide to `prs` using `slide_kit`. Do NOT re-create prior slides or call `prs.save()`.
2. NO CONCEPT BLEED: Focus purely on the assigned concept. Do not repeat earlier concepts, titles, or overview text.
3. VISUAL ANCHORING: Every concept slide MUST have a rendered graphic (flowchart, architecture diagram, confusion matrix, distribution, custom plot, or artifact comparison). Never use empty slides or put Python code inside text cards as a visual substitute.
4. DOMAIN GROUNDING: Include the provided domain application so students understand how the computational principle directly solves the real-world problem.
5. ARTIFACT UTILIZATION: If `artifacts` are relevant and available in the REPL (`artifacts['raw_sample']`, `artifacts['mask_sample']`, etc.), embed or blend them as authentic examples.
"""


def build_concept_slide_prompt(
    concept: DiscretizedConcept,
    total_concepts: int,
    deck_title: str,
    domain_subtitle: str,
    recipe_code: str,
    previous_slides_summary: str,
    artifacts: Optional[Dict[str, str]] = None
) -> str:
    """Builds prompt for synthesizing Python code for a single concept slide."""
    artifact_details = []
    if artifacts:
        for k, v in artifacts.items():
            if v:
                artifact_details.append(f"- `artifacts['{k}']` -> '{v}'")
    artifact_str = "\n".join(artifact_details) if artifact_details else "No artifact files available."

    return f"""DECK: '{deck_title}' | Domain Context: '{domain_subtitle}'

PREVIOUS SLIDES ALREADY CONSTRUCTED IN THIS DECK (Do not duplicate; build upon their concepts):
{previous_slides_summary or 'No concept slides created yet.'}

TARGET CONCEPT TO CONSTRUCT (CONCEPT #{concept.concept_index} OF {total_concepts}):
- Title: '{concept.title}'
- Algorithmic Principle: {concept.algorithmic_principle}
- Domain Application: {concept.domain_application}
- Pipeline Data Flow / Contract: {concept.pipeline_data_flow}
- Key Takeaways:
{chr(10).join([f"  * {t}" for t in concept.key_takeaways])}

VISUAL SPECIFICATION:
- Category: {concept.visual_spec.category}
- Visual Directive: {concept.visual_spec.visual_idea}
- Use Artifact: {concept.visual_spec.use_artifact} (Type: {concept.visual_spec.artifact_type or 'None'})

AVAILABLE PIPELINE ARTIFACTS IN REPL SCOPE:
{artifact_str}

RELEVANT VISUAL RECIPE:
```python
{recipe_code or '# Use standard visual_kit or matplotlib calls'}
```

DIRECTIVE:
Write executable Python code wrapped in SingleSlideCodeSchema that:
1. Renders the required visual graphic using `visual_kit`, `matplotlib`, or `artifacts`.
2. Appends EXACTLY ONE slide to `prs` using `slide_kit.add_split_slide` or `slide_kit.add_hero_graphic`.
3. Ensures high contrast, clear domain context, and detailed pedagogical bullet points."""


