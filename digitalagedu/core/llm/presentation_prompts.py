import ast
import difflib
from typing import Dict, Any, List, Optional, Literal, Tuple
from pydantic import BaseModel, Field, field_validator

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


class EvidenceItem(BaseModel):
    """One real number from the pipeline run, shown as a metric card on the slide."""
    label: str = Field(..., description="Short label, e.g. 'Overall accuracy' or 'Rarest class'.")
    value: str = Field(..., description="The exact number from telemetry with an optional unit, at most 16 characters, "
                                        "e.g. '94.5%' or '13 images'. Class names go in `context`, never here.")
    context: str = Field(..., description="Where it comes from or what it means, e.g. 'Apple___Cedar_apple_rust'.")

    @field_validator("value")
    @classmethod
    def _is_a_short_number(cls, v: str) -> str:
        # Shown in a large font on a small card: a class name there wraps and clips the card (run dc3f8936)
        if not any(ch.isdigit() for ch in v) or len(v) > 16:
            raise ValueError("`value` must be a number of at most 16 characters (e.g. '13 images'); put names in `context`")
        return v


_PLACEHOLDER_RULES = {"", "n/a", "na", "none", "n.a.", "-", "tbd", "confidential", "not applicable"}


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
        description="2 to 4 full sentences that each explain a MECHANISM (why/how it works), not a task step. "
                    "Bad: 'Load images as numpy arrays.' Good: 'Chlorotic tissue lowers G relative to R, so ExG drops before lesions are visible.'"
    )
    formula_or_rule: str = Field(
        ...,
        description="The exact equation or precise rule that `code_function` computes, with the same constants as the code "
                    "(e.g. 'ExG = 2G - R - B', 'IoU = |A ∩ B| / |A ∪ B|', 'imbalance ratio = n_max / n_min')."
    )

    @field_validator("formula_or_rule")
    @classmethod
    def _is_a_real_rule(cls, v: str) -> str:
        # Placeholders like 'N/A' and 'Confidential' reached the slides' RULE banner (run dc3f8936)
        if v.strip().lower().rstrip(".") in _PLACEHOLDER_RULES or len(v.strip()) < 5:
            raise ValueError("`formula_or_rule` must be the actual equation or rule the code computes, not a placeholder")
        return v
    real_evidence: List[EvidenceItem] = Field(
        ...,
        min_length=1,
        max_length=3,
        description="1 to 3 numbers copied from THIS run's telemetry that make the concept concrete. Never invent numbers."
    )
    code_function: str = Field(
        ...,
        description="Name of the function or class in the verified reference solution that implements this concept (must be one of the listed names)."
    )
    misconception: str = Field(
        ...,
        description="One common student misconception about this concept and why it is wrong."
    )
    speaker_notes: str = Field(
        ...,
        description="3 to 6 sentences the teacher says over this slide: the mechanism, how the real numbers arise, and how the code implements it."
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
5. TECHNICAL DEPTH (every concept):
   - `formula_or_rule`: the exact equation or rule that `code_function` computes (same constants as its code), not a description of it.
   - `real_evidence`: numbers copied verbatim from the PHASE 1 PIPELINE TELEMETRY below (accuracy, class counts, per-class F1, confusion pairs). Never invent or round them differently.
   - `code_function`: a function/class name that exists in the verified reference solution.
   - `key_takeaways`: mechanisms (why/how), never task steps like 'Load the CSV'.
   - `misconception` and `speaker_notes`: what a teacher would actually say.
"""


def solution_symbols(solution_code: str) -> List[str]:
    """Names of the top-level functions and classes (and their methods) in the verified solution."""
    try:
        tree = ast.parse(solution_code or "")
    except SyntaxError:
        return []
    return [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]


def solution_excerpt(solution_code: str, name: str, max_lines: int = 9, width: int = 64) -> Tuple[Optional[str], str]:
    """(resolved name, source) of the named function/class, matching the closest name if the planner misspelled it.
    Cut to `max_lines` lines as displayed in the slide's code box, where lines longer than `width` wrap."""
    try:
        tree = ast.parse(solution_code or "")
    except SyntaxError:
        return None, ""
    nodes = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    match = name if name in nodes else next(iter(difflib.get_close_matches(name or "", list(nodes), n=1, cutoff=0.5)), None)
    if not match:
        return None, ""
    lines = (ast.get_source_segment(solution_code, nodes[match]) or "").splitlines()
    rows = [max(1, -(-len(line) // width)) for line in lines]  # wrapped display rows per line (ceil)
    if sum(rows) <= max_lines:
        return match, "\n".join(lines)
    shown, used = [], 0
    for line, n in zip(lines, rows):
        if used + n > max_lines - 1:  # keep a row for "..."
            break
        shown.append(line)
        used += n
    return match, "\n".join(shown + ["    ..."])


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
Functions/classes available for `code_function`: {', '.join(solution_symbols(compact_solution)) or 'none'}

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
6. REAL DATA ONLY: Every chart plots values read from `telemetry`, `artifacts` (images, `artifacts['results_csv']`) or the REAL RUN DATA in the prompt. Never use `np.random`, hardcoded "sample"/"dummy"/"simulated" data, or class names that are not in this dataset. Code that fabricates data is rejected before it runs.
7. LAYOUT: Build the slide with the LAYOUT TEMPLATE in the prompt. Keep its formula, evidence cards, code box, misconception and takeaway parts; you write the chart.
"""


CONCEPT_SLIDE_LAYOUT_TEMPLATE = '''slide = slide_kit.create_slide(prs)
slide_kit.add_header(slide, tag=f"CONCEPT {concept.concept_index}", title=concept.title, subtitle=concept.domain_application)

# --- YOUR PART: a chart of REAL values (telemetry / artifacts / pd.read_csv(artifacts["results_csv"])) ---
fig, ax = plt.subplots(figsize=(7.0, 3.8))
visual_kit.apply_dark_theme(fig, ax)
# ... plot the real data for this concept here ...
fig.tight_layout()
plt.savefig("concept_{index}.png", dpi=150, facecolor=fig.get_facecolor())
plt.close(fig)
slide_kit.add_image(slide, 0.6, 1.75, 6.5, 3.55, image_path="concept_{index}.png")

# --- Keep: the rule, misconception, real numbers, verified code and mechanisms ---
slide_kit.add_callout_banner(slide, 0.6, 5.45, 6.5, 0.85, text=concept.formula_or_rule, title="RULE")
slide_kit.add_callout_banner(slide, 0.6, 6.4, 6.5, 0.85, text=concept.misconception, title="COMMON MISCONCEPTION")
for i, ev in enumerate(concept.real_evidence[:2]):
    slide_kit.add_metric_card(slide, 7.35 + i * 2.8, 1.75, 2.65, 1.15, label=ev.label, value=ev.value, subtext=ev.context)
slide_kit.add_code_box(slide, 7.35, 3.05, 5.45, 2.05, code=solution_excerpt, title=code_function_name + "()  - verified solution")
slide_kit.add_callout_column(slide, [("Why", concept.key_takeaways[0]), ("How", concept.key_takeaways[-1])], x=7.35, y=5.25, w=5.45, h=2.05)'''


def build_concept_slide_prompt(
    concept: DiscretizedConcept,
    total_concepts: int,
    deck_title: str,
    domain_subtitle: str,
    recipe_code: str,
    previous_slides_summary: str,
    artifacts: Optional[Dict[str, str]] = None,
    telemetry: Optional[Dict[str, Any]] = None,
    code_function_name: Optional[str] = None,
) -> str:
    """Builds prompt for synthesizing Python code for a single concept slide."""
    artifact_details = []
    if artifacts:
        for k, v in artifacts.items():
            if v:
                artifact_details.append(f"- `artifacts['{k}']` -> '{v}'")
    artifact_str = "\n".join(artifact_details) if artifact_details else "No artifact files available."
    telemetry = telemetry if isinstance(telemetry, dict) else {}
    run_summary_keys = list(telemetry.get("run_summary", {})) if isinstance(telemetry.get("run_summary"), dict) else []
    evidence = "\n".join(f"  * {e.label}: {e.value} ({e.context})" for e in concept.real_evidence)

    return f"""DECK: '{deck_title}' | Domain Context: '{domain_subtitle}'

PREVIOUS SLIDES ALREADY CONSTRUCTED IN THIS DECK (Do not duplicate; build upon their concepts):
{previous_slides_summary or 'No concept slides created yet.'}

TARGET CONCEPT TO CONSTRUCT (CONCEPT #{concept.concept_index} OF {total_concepts}):
- Title: '{concept.title}'
- Algorithmic Principle: {concept.algorithmic_principle}
- Domain Application: {concept.domain_application}
- Pipeline Data Flow / Contract: {concept.pipeline_data_flow}
- Key Takeaways (mechanisms):
{chr(10).join([f"  * {t}" for t in concept.key_takeaways])}
- Rule / Formula: {concept.formula_or_rule}
- Real evidence from this run:
{evidence}
- Implemented by: `{code_function_name or concept.code_function}` in the verified solution (its source is in `solution_excerpt`)
- Common misconception: {concept.misconception}
All of these are available in the REPL as `concept` (fields above), `solution_excerpt` and `code_function_name`.

VISUAL SPECIFICATION:
- Category: {concept.visual_spec.category}
- Visual Directive: {concept.visual_spec.visual_idea}
- Use Artifact: {concept.visual_spec.use_artifact} (Type: {concept.visual_spec.artifact_type or 'None'})

REAL RUN DATA (plot these values; never invent data):
{build_telemetry_prompt_summary(telemetry)}
In code, read them from `telemetry` (keys: {list(telemetry) or 'none'}; telemetry['run_summary'] keys: {run_summary_keys or 'none'}).

AVAILABLE PIPELINE ARTIFACTS IN REPL SCOPE:
{artifact_str}

RELEVANT VISUAL RECIPE (use only for how to draw the chart; build the slide with the template below):
```python
{recipe_code or '# Use standard visual_kit or matplotlib calls'}
```

LAYOUT TEMPLATE (copy it; replace only the chart part with a plot of real data):
```python
{CONCEPT_SLIDE_LAYOUT_TEMPLATE.replace("{index}", str(concept.concept_index))}
```

DIRECTIVE:
Write executable Python code that adds EXACTLY ONE slide to `prs` following the layout template, with a chart of this run's real data for concept #{concept.concept_index}."""


