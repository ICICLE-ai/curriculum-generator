from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field

from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.telemetry import build_telemetry_prompt_summary

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

    telemetry_summary = build_telemetry_prompt_summary(telemetry if isinstance(telemetry, dict) else {})

    # Summarize milestone subsystems
    subsystems_info = []
    if getattr(problem_formulation, "milestone_subsystems", None):
        for sub in problem_formulation.milestone_subsystems:
            comp_sigs = [f"{c.kind} {c.name}: {c.signature}" for c in getattr(sub, "components", [])]
            subsystems_info.append(f"- Milestone {sub.milestone_num}: {sub.title} ({sub.objective}) -> Components: {', '.join(comp_sigs)}")
    subsystems_text = "\n".join(subsystems_info) if subsystems_info else "Core computational pipeline"

    # Artifact inventory
    artifact_lines = []
    if artifacts:
        for k, v in artifacts.items():
            if v:
                artifact_lines.append(f"- `{k}`: {v}")
    artifact_str = "\n".join(artifact_lines) if artifact_lines else "- No local sample image fixtures registered."

    compact_solution = solution_code.strip()

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

{telemetry_summary}

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
Write executable Python code that:
1. Renders the required visual graphic using `visual_kit`, `matplotlib`, or `artifacts`.
2. Appends EXACTLY ONE slide to `prs` using `slide_kit.add_split_slide` or `slide_kit.add_hero_graphic`.
3. Ensures high contrast, clear domain context, and detailed pedagogical bullet points."""


