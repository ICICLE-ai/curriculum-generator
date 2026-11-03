import ast
import difflib
from typing import Dict, Any, List, Optional, Literal, Tuple
from pydantic import BaseModel, Field, field_validator, model_validator

from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.telemetry import build_telemetry_prompt_summary

SUBPROCESS_TIMEOUT_SECONDS = 180


class ConceptVisualSpec(BaseModel):
    """Specification of the visual graphic or animation for one slide."""
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


def _within_slide_budget(v: str, field: str, limit: int) -> str:
    # Slide text sits in fixed-size boxes. slide_kit shrinks and trims small overruns, so only
    # reject clear ones: an exact limit failed a whole deck over 141 vs 140 characters (run 362c473a)
    if len(v) > limit * 1.5:
        raise ValueError(f"`{field}` is {len(v)} characters but its slide box fits {limit}; rewrite it in at most {limit} characters")
    return v


class EvidenceItem(BaseModel):
    """One real number from the pipeline run, shown on a goal or application slide."""
    label: str = Field(..., description="Short label of at most 30 characters, e.g. 'Overall accuracy' or 'Rarest class'.")
    value: str = Field(..., description="The exact number from telemetry with an optional unit, at most 16 characters, "
                                        "e.g. '94.5%' or '13 images'. Class names go in `context`, never here.")
    context: str = Field(..., description="Where it comes from or what it means, at most 40 characters, e.g. 'Apple___Cedar_apple_rust'.")

    @field_validator("label", "context")
    @classmethod
    def _fits_metric_card(cls, v: str, info) -> str:
        return _within_slide_budget(v, info.field_name, {"label": 30, "context": 40}[info.field_name])

    @field_validator("value")
    @classmethod
    def _is_a_short_number(cls, v: str) -> str:
        # Shown in a large font on a small card: a class name there wraps and clips the card (run dc3f8936)
        if not any(ch.isdigit() for ch in v) or len(v) > 16:
            raise ValueError("`value` must be a number of at most 16 characters (e.g. '13 images'); put names in `context`")
        return v


# The deck teaches in this order: the data and the task, the methods, each method in depth, why they are needed,
# then this run's application of them (the only place code appears)
SECTION_ORDER = ("goal", "overview", "method", "why", "application")


class LessonSlide(BaseModel):
    """One slide that teaches one idea."""
    section: Literal["goal", "overview", "method", "why", "application"] = Field(
        ...,
        description="goal: this run's data and what the module must produce from it. overview: the methods and how they "
                    "connect. method: explains one method. why: why these methods are needed. application: how this run "
                    "applies them to the domain (results, artifacts, verified code)."
    )
    method: Optional[str] = Field(
        default=None,
        description="For section 'method': the entry of `methods` this slide explains, copied exactly. None otherwise."
    )
    title: str = Field(..., description="Slide title of at most 65 characters.")
    teaching_point: str = Field(
        ...,
        description="The ONE idea a student must take away from this slide, as a full sentence. Guides the slide; not printed."
    )
    on_slide_text: List[str] = Field(
        ...,
        min_length=1,
        max_length=4,
        description="1 to 4 short lines of at most 110 characters each: the only words on the slide besides chart and "
                    "diagram labels. No paragraphs; the explanation goes in `speaker_notes`."
    )
    visual: ConceptVisualSpec = Field(
        ...,
        description="The slide's graphic. Method slides: a conceptual diagram of the mechanism (architecture, data flow, "
                    "before/after). Goal and application slides: this run's real data or artifacts."
    )
    evidence: List[EvidenceItem] = Field(
        default_factory=list,
        max_length=3,
        description="0 to 3 numbers copied from THIS run's telemetry. Required on goal and application slides. Never invent numbers."
    )
    code_function: Optional[str] = Field(
        default=None,
        description="Application slides only: a function/class in the verified reference solution (one of the listed names) "
                    "whose code the slide shows. None on every other slide."
    )
    speaker_notes: str = Field(
        ...,
        description="4 to 8 sentences the teacher says over this slide: the full explanation the slide text leaves out."
    )

    @field_validator("title")
    @classmethod
    def _title_fits(cls, v: str) -> str:
        return _within_slide_budget(v, "title", 65)

    @field_validator("on_slide_text")
    @classmethod
    def _lines_fit(cls, v: List[str]) -> List[str]:
        for line in v:
            _within_slide_budget(line, "on_slide_text", 110)
        return v


class LessonPlan(BaseModel):
    """The deck as an ordered lesson: goal -> overview -> method -> why -> application."""
    deck_title: str = Field(..., description="High-level presentation title.")
    domain_subtitle: str = Field(..., description="Domain problem and its real-world motivation, one sentence.")
    methods: List[str] = Field(
        ...,
        min_length=2,
        max_length=4,
        description="The 2 to 4 technologies or methods this module uses, in the order they are applied "
                    "(e.g. 'DINOv2 self-supervised ViT', 'Logistic regression probe')."
    )
    slides: List[LessonSlide] = Field(
        ...,
        min_length=10,
        max_length=16,
        description="10 to 16 slides in teaching order: goal, overview, at least 2 method slides per method, why, application."
    )
    takeaways: List[str] = Field(..., min_length=2, max_length=4, description="2 to 4 points for the closing slide.")

    @model_validator(mode="after")
    def _follows_the_lesson_flow(self) -> "LessonPlan":
        sections = [s.section for s in self.slides]
        problems = []
        ranks = [SECTION_ORDER.index(s) for s in sections]
        if ranks != sorted(ranks):
            problems.append("slides must follow the section order goal -> overview -> method -> why -> application")
        missing = [s for s in SECTION_ORDER if s not in sections]
        if missing:
            problems.append(f"missing sections: {missing}")
        for m in self.methods:
            n = sum(1 for s in self.slides if s.section == "method" and s.method == m)
            if n < 2:
                problems.append(f"method '{m}' has {n} explanation slides; give it at least 2 (what it is, then how it works)")
        unknown = sorted({str(s.method) for s in self.slides if s.section == "method"} - set(self.methods))
        if unknown:
            problems.append(f"method slides name {unknown}, which are not in `methods`; copy the names exactly")
        coded = [s.title for s in self.slides if s.code_function and s.section != "application"]
        if coded:
            problems.append(f"only application slides may set `code_function`; remove it from {coded}")
        no_data = [s.title for s in self.slides if s.section in ("goal", "application") and not s.evidence]
        if no_data:
            problems.append(f"goal and application slides need at least one real number in `evidence`: {no_data}")
        if problems:
            raise ValueError("; ".join(problems))
        return self


LESSON_PLANNER_SYSTEM = """You are an expert computing professor planning one week's lecture deck. The slides are the
main way students learn this material, so they must teach, not summarize.

TEACHING ORDER (each section is required, in this order):
1. goal (1-2 slides): Show the data first. Real samples and classes from this run, and exactly what the module must
   produce from them (the output and how success is measured). Students understand the problem before any method.
2. overview (1 slide): Name the methods and how they connect, in plain language, before any detail.
3. method (at least 2 slides per method, methods in the order they are used): Never use a method before explaining it.
   First what it is (where it comes from, the core idea, an intuition), then how it works (inputs and outputs, the
   mechanism, its key equation in plain text). Define every term a student may not know. No code and no run numbers.
4. why (1-2 slides): Why these methods are needed here: what a naive approach gets wrong for this domain problem.
5. application (2-4 slides): How this run applied the methods to the domain: real results from the telemetry,
   artifacts, the verified code (`code_function`), and what the numbers mean for the domain.

RULES:
- One idea per slide. `on_slide_text` holds a few short lines; the full explanation goes in `speaker_notes`.
- Facts about methods must be correct; when unsure, say less rather than guess.
- Numbers in `evidence` are copied verbatim from the PHASE 1 PIPELINE TELEMETRY. Never invent or round them differently.
- `code_function` only on application slides, and only names from the verified solution.
- Every slide has a visual: conceptual diagrams for methods, real data or artifacts for goal and application.
- Formulas are plain text (e.g. 'IoU = |A ∩ B| / |A ∪ B|'), never LaTeX: slides cannot render it."""


def solution_symbols(solution_code: str) -> List[str]:
    """Names of the top-level functions and classes (and their methods) in the verified solution."""
    try:
        tree = ast.parse(solution_code or "")
    except SyntaxError:
        return []
    return [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]


def solution_excerpt(solution_code: str, name: str, max_lines: int = 8, width: int = 64) -> Tuple[Optional[str], str]:
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


def _artifact_lines(artifacts: Optional[Dict[str, str]], fmt: str) -> str:
    lines = [fmt.format(k=k, v=v) for k, v in (artifacts or {}).items() if v]
    return "\n".join(lines) if lines else "- No sample image artifacts available."


def build_lesson_plan_prompt(
    module: Module,
    problem_formulation: ProblemStatementSchema,
    solution_code: str,
    telemetry: Dict[str, Any],
    artifacts: Optional[Dict[str, str]] = None
) -> str:
    """Prompt for the lesson planner: the module, its verified solution, this run's telemetry and artifacts."""
    title = problem_formulation.title or module.title
    domain_ctx = problem_formulation.domain_context or module.context
    objectives = problem_formulation.learning_objectives or []
    focus = problem_formulation.suggested_focus or "Deep Learning & Model Architecture"
    subsystems = [
        f"- Milestone {sub.milestone_num}: {sub.title} ({sub.objective}) -> Components: "
        + ", ".join(f"{c.kind} {c.name}: {c.signature}" for c in getattr(sub, "components", []))
        for sub in (getattr(problem_formulation, "milestone_subsystems", None) or [])
    ]
    compact_solution = solution_code.strip()

    return f"""MODULE: {title} (Week {module.week}) | Difficulty: {module.difficulty.title()}
DOMAIN APPLICATION: {domain_ctx}
CORE PROBLEM DIRECTIVE: {problem_formulation.problem_statement or ""}
PEDAGOGICAL FOCUS: {focus}

LEARNING OBJECTIVES:
{chr(10).join(f"- {o}" for o in objectives)}

PIPELINE & SUBSYSTEM ARCHITECTURE:
{chr(10).join(subsystems) or "Core computational pipeline"}

VERIFIED REFERENCE SOLUTION (what students implement):
```python
{compact_solution}
```
Functions/classes available for `code_function`: {', '.join(solution_symbols(compact_solution)) or 'none'}

{build_telemetry_prompt_summary(telemetry if isinstance(telemetry, dict) else {})}

AVAILABLE AUTHENTIC PIPELINE ARTIFACTS:
{_artifact_lines(artifacts, "- `{k}`: {v}")}

DIRECTIVE:
Plan this week's lecture deck as 10 to 16 slides following the teaching order. Identify the methods the module relies
on, explain each one before it is used, and finish by applying them to this run's data."""


SLIDE_BUILDER_SYSTEM = """You are an expert Presentation Designer and Python Developer.
You build one PowerPoint lecture slide at a time in a stateful Python REPL using `slide_kit` and `visual_kit`.
The deck is the students' main way to learn this material: each slide teaches ONE idea, clearly and visually.

CRITICAL INVARIANTS:
1. EXACTLY ONE SLIDE: Your code must add EXACTLY ONE slide to `prs` using `slide_kit`. Do NOT re-create prior slides or call `prs.save()`.
2. LITTLE TEXT: Show the slide's `on_slide_text` lines (`slide_spec.on_slide_text`; you may shorten them) plus labels
   inside the graphic. No paragraphs: the teacher explains the rest from the speaker notes.
3. A GRAPHIC ON EVERY SLIDE: method slides get a conceptual diagram that makes the mechanism visible (boxes and arrows,
   an architecture sketch, a before/after); goal and application slides show this run's data or artifact images.
4. REAL DATA ONLY: Any chart of measurements plots values read from `telemetry`, `artifacts` (images,
   `artifacts['results_csv']`) or the REAL RUN DATA in the prompt. Conceptual diagrams illustrate ideas and need no
   numbers. Never use `np.random` or "sample"/"dummy"/"simulated" data. Code that fabricates data is rejected before it runs.
5. CODE: Only application slides may show code, and only the verified `solution_excerpt`, never code you wrote.
6. ARTIFACTS: If `artifacts` (`artifacts['raw_sample']`, `artifacts['mask_sample']`, ...) fit the slide, use them as authentic examples.
7. FREE LAYOUT: Choose the layout this slide needs and vary it from earlier slides. The example in the prompt is one option.
8. GEOMETRY: The slide is 13.33 x 7.5 in. Keep everything inside x 0.5-12.8 and y 0.4-7.1; `add_header` uses y 0.5-1.7.
   slide_kit shrinks text that does not fit its box, so prefer fewer words in bigger boxes. Elements must not overlap.
9. A reviewer checks your slide's geometry and a screenshot of it and may send fixes; apply them all and keep what already worked.
"""


SLIDE_KIT_REFERENCE = """slide = slide_kit.create_slide(prs)            # always first; adds the dark background
slide_kit.add_header(slide, tag, title, subtitle=None)               # pill + title at y 0.5-1.7
slide_kit.add_image(slide, x, y, w, h, image_path, caption=None)     # keeps the image's aspect ratio, centered in the box
slide_kit.add_card(slide, x, y, w, h, title=None, body=None, accent_color=None)
slide_kit.add_callout_banner(slide, x, y, w, h, text, title)         # gold-accent card for a rule or warning
slide_kit.add_callout_column(slide, [(title, text), ...], x, y, w, h)  # stacked cards
slide_kit.add_metric_card(slide, x, y, w, h, label, value, subtext=None)
slide_kit.add_badge_row(slide, x, y, [(label, value), ...], item_w=2.75, h=0.9)
slide_kit.add_step_flow(slide, x, y, w, h, steps=[...])              # left-to-right pipeline stages
slide_kit.add_code_box(slide, x, y, w, h, code=solution_excerpt, title=...)
slide_kit.add_table(slide, x, y, w, h, headers=[...], rows=[[...], ...])
slide_kit.add_artifact_comparison(slide, x, y, w, h, original_path, processed_path)
Colors for matplotlib: visual_kit.Colors.{BG, CARD, BORDER, TEXT, MUTED, CYAN, INDIGO, EMERALD, CORAL, GOLD, PURPLE}
Colors for slide_kit: slide_kit.Theme.{ACCENT_CYAN, ACCENT_INDIGO, ACCENT_EMERALD, ACCENT_CORAL, ACCENT_GOLD, TEXT_PRIMARY, TEXT_MUTED}"""


# One example layout shown to the slide builder (a method slide with a drawn diagram); slides are free to differ
EXAMPLE_SLIDE_LAYOUT = '''slide = slide_kit.create_slide(prs)
slide_kit.add_header(slide, tag="METHOD", title=slide_spec.title)

# A conceptual diagram: boxes and arrows that make the mechanism visible (no measurements needed)
fig, ax = plt.subplots(figsize=(8.0, 4.6))
visual_kit.apply_dark_theme(fig, ax)
ax.axis("off")
steps = ["Leaf image", "Encoder", "Features"]
for i, step in enumerate(steps):
    ax.text(0.15 + i * 0.35, 0.5, step, ha="center", va="center", fontsize=14, color=visual_kit.Colors.TEXT,
            bbox=dict(boxstyle="round,pad=0.6", fc=visual_kit.Colors.CARD, ec=visual_kit.Colors.CYAN))
    if i < len(steps) - 1:
        ax.annotate("", xy=(0.33 + i * 0.35, 0.5), xytext=(0.27 + i * 0.35, 0.5),
                    arrowprops=dict(arrowstyle="->", color=visual_kit.Colors.MUTED, lw=2))
plt.savefig("slide_{index}.png", dpi=150, facecolor=fig.get_facecolor())
plt.close(fig)
slide_kit.add_image(slide, 0.6, 1.9, 7.6, 4.9, image_path="slide_{index}.png")
slide_kit.add_card(slide, 8.5, 1.9, 4.3, 4.9, title="Key points",
                   body="\\n".join("• " + line for line in slide_spec.on_slide_text))'''


# What each section's slides must do, given to the builder with the slide's own spec
SECTION_GUIDANCE = {
    "goal": "Show the data and the task: real sample images from `artifacts`, the classes or class counts from "
            "telemetry, and what the module must output and how success is measured.",
    "overview": "A map of the methods and how data flows through them (e.g. `add_step_flow` or a drawn pipeline).",
    "method": "Explain the method's idea with a conceptual diagram. No run numbers and no code on this slide.",
    "why": "Contrast a naive approach with the method for this domain problem: what goes wrong without it.",
    "application": "Show how this run applied the methods: real results from telemetry, artifact images, and, if "
                   "`code_function_name` is set, the verified `solution_excerpt` in a code box.",
}


def build_lesson_slide_prompt(
    slide: LessonSlide,
    plan: LessonPlan,
    index: int,
    recipe_code: str,
    artifacts: Optional[Dict[str, str]] = None,
    telemetry: Optional[Dict[str, Any]] = None,
    code_function_name: Optional[str] = None,
    solution_code_excerpt: str = "",
) -> str:
    """Prompt for the code of plan slide number `index` (1-based)."""
    telemetry = telemetry if isinstance(telemetry, dict) else {}
    run_summary_keys = list(telemetry.get("run_summary", {})) if isinstance(telemetry.get("run_summary"), dict) else []
    outline = "\n".join(
        f"{n}. [{s.section}] {s.title}" + ("   <- THIS SLIDE" if n == index else "") for n, s in enumerate(plan.slides, 1)
    )
    evidence = "\n".join(f"  * {e.label}: {e.value} ({e.context})" for e in slide.evidence) or "  (none)"
    method_line = f"\n- Method explained: {slide.method}" if slide.method else ""
    data_block = "" if slide.section == "method" else f"""
REAL RUN DATA (plot these values; never invent data):
{build_telemetry_prompt_summary(telemetry)}
In code, read them from `telemetry` (keys: {list(telemetry) or 'none'}; telemetry['run_summary'] keys: {run_summary_keys or 'none'}).
"""
    code_block = "" if not (slide.section == "application" and code_function_name) else f"""
VERIFIED CODE (in the REPL as `solution_excerpt`; function `code_function_name` = '{code_function_name}'):
```python
{solution_code_excerpt}
```
"""
    return f"""DECK: '{plan.deck_title}' | Domain: '{plan.domain_subtitle}' | Methods: {', '.join(plan.methods)}

DECK OUTLINE (each slide teaches one idea; do not repeat other slides):
{outline}

THIS SLIDE (in the REPL as `slide_spec`):
- Section: {slide.section} -> {SECTION_GUIDANCE[slide.section]}{method_line}
- Title: '{slide.title}'
- Teaching point (what a student must take away): {slide.teaching_point}
- On-slide text (the only words besides graphic labels):
{chr(10).join(f"  * {t}" for t in slide.on_slide_text)}
- Real evidence for this slide:
{evidence}

VISUAL:
- Category: {slide.visual.category}
- Directive: {slide.visual.visual_idea}
- Use Artifact: {slide.visual.use_artifact} (Type: {slide.visual.artifact_type or 'None'})
{data_block}
AVAILABLE PIPELINE ARTIFACTS IN REPL SCOPE:
{_artifact_lines(artifacts, "- `artifacts['{k}']` -> '{v}'")}
{code_block}
RELEVANT VISUAL RECIPE (how to draw this kind of graphic):
```python
{recipe_code or '# Use standard visual_kit or matplotlib calls'}
```

SLIDE KIT:
```python
{SLIDE_KIT_REFERENCE}
```

ONE EXAMPLE LAYOUT (do not copy it; design the layout this slide needs and vary it from earlier slides):
```python
{EXAMPLE_SLIDE_LAYOUT.replace("{index}", str(index))}
```

DIRECTIVE:
Write executable Python code that adds EXACTLY ONE slide to `prs` teaching slide {index}'s point."""


class SlideReview(BaseModel):
    """A vision model's verdict on one rendered slide."""
    acceptable: bool = Field(..., description="True when a teacher could show this slide to students as is.")
    issues: List[str] = Field(
        default_factory=list,
        description="Concrete fixes, each naming the element and what to change (e.g. 'The bar chart's x labels overlap; "
                    "rotate them 45 degrees'). Empty when acceptable.",
    )


SLIDE_REVIEW_SYSTEM = """You review one lecture slide from a screenshot, for a computing course taught with real data.
The slides are the students' main way to learn, so each must teach its one idea clearly.
Reject the slide only for problems a student would notice:
- text cut off, overlapping other elements, running off the slide, or too small to read from the back of a room
- a chart that is empty, unreadable (tiny or overlapping labels, no axis meaning), or does not show what the caption claims
- paragraphs or more text than a student can read during the explanation (a few short lines is the limit)
- a factual error about the method or concept
- the same layout as an earlier slide shown to you (give a concrete alternative)
- a slide that does not teach its point
Accept good slides; do not ask for changes of taste. Every issue must be a concrete, actionable fix."""


def build_slide_review_messages(slide_title: str, focus: str, new_slide_url: str, earlier_slide_urls: List[str]) -> List[Dict[str, Any]]:
    """Chat messages showing the new slide and the earlier slides (data URLs) to the reviewer."""
    content: List[Dict[str, Any]] = [
        {"type": "text", "text": f"Slide: '{slide_title}'. It should teach: {focus}\nNEW SLIDE to review:"},
        {"type": "image_url", "image_url": {"url": new_slide_url}},
    ]
    if earlier_slide_urls:
        content.append({"type": "text", "text": "EARLIER SLIDES in this deck (for variety; do not review them):"})
        content += [{"type": "image_url", "image_url": {"url": u}} for u in earlier_slide_urls]
    return [{"role": "system", "content": SLIDE_REVIEW_SYSTEM}, {"role": "user", "content": content}]
