# Task: Integrate AI-Directed Animation and Rich Visual Generation into the Curriculum Generator

## Context

We are developing the Smart Curriculum Designer in the `ICICLE-ai/curriculum-generator` repository. The backend is Python-based and uses vLLM-served open-source LLMs to generate educational curriculum and PowerPoint presentations.

The existing presentation generation pipeline uses:

- `PresentationDesigner` to prompt an LLM to generate Python code that constructs a presentation.
- `python-pptx` to create native PowerPoint slides.
- `slide_kit.py` to provide reusable presentation composition utilities.
- Existing curriculum-generation agents, computational artifacts, model telemetry, reference solutions, and educational content as inputs to the presentation generation process.

The current approach gives the LLM creative freedom over slide content and layout, but its visual capabilities are primarily limited to text, cards, metrics, tables, and simple diagrams.
The current approach gives the LLM creative freedom over slide content and layout, but its visual capabilities are primarily limited to static text, cards, metrics, tables, and simple step flows.

## Objective

---

Extend the existing pipeline so the LLM can independently decide when and how to use high-quality animations, scientific visualizations, images, diagrams, and charts to create visually compelling educational presentations.

## Objective & Architectural Philosophy

**The LLM must remain responsible for deciding what to teach, which visual medium best explains each concept, how slides should be composed, and when animations are useful.**
Extend the existing pipeline so the LLM can independently decide when and how to use high-quality animations, scientific visualizations, images, diagrams, and charts to create visually compelling, domain-agnostic educational presentations.

Do not replace this with a fixed collection of predefined slide templates. Build reusable rendering tools that the LLM can combine creatively based on the subject matter, educational objectives, available artifacts, and target audience.

### Core Tenets:
1. **The LLM Directs the Narrative and Visual Medium**: The LLM remains responsible for deciding what to teach, which visual medium best explains each concept, how slides should be composed, and when animations are useful.
2. **Domain-Agnostic Primitives**: The pipeline supports diverse domains (agriculture, dermatology, disaster response, food classification, etc.). All visual tools must operate on abstract ML, mathematical, and computer vision concepts (e.g., artifact morphs, 3D loss landscapes, latent cluster projections, confusion matrices, architecture flows) rather than domain-specific hardcoded labels.
3. **Composable Primitives (Lego Bricks) Over Rigid Templates**: Avoid replacing current slides with fixed monolithic slide layouts (e.g., "Layout A", "Template 1"). Instead, provide small, parameterized tools that the LLM can freely position across the 16:9 canvas alongside code, metrics, and explanatory text.
4. **No Fallback Bloat & Fail-Fast Slide Execution**: We do NOT maintain layers of fake/mock fallback decks or stub visuals (avoiding bloat code). Every module must produce a complete deck built from a sandbox-verified solution: an unverified solution, a slide that still fails after its self-healing retry, or a deck that cannot be saved crashes the pipeline.
5. **Dedicated Visuals Subsystem**: All slide visual generation services reside in `digitalagedu/core/llm/visuals/`.
6. **HPC Headless & Container Compatibility**: The system must run reliably inside headless environments (SDSC Expanse Singularity containers, Docker, local dev) without requiring an interactive X-server.

The implementation must work within our existing pipeline and remain compatible with our Python backend and vLLM-served models.
-------------------------------------------------------------------------------------------------------------------------------

## 1. Inspect the Existing Architecture First

## 1. Two-Tier Decoupled Toolkit Architecture

Before changing code, inspect the repository and trace the complete presentation-generation workflow.
To give the LLM full composition autonomy without forcing it to write low-level rendering code (e.g., manual VTK vertices, raw Cairo paths, or low-level framebuffers), the visual system is split into two distinct tiers:

Pay particular attention to:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                     TIER 1: Visual Asset Producers (visual_kit)                │
│       • Generates domain-agnostic media files (.mp4, .gif, .png) from data       │
│                                                                                 │
│   • visual_kit.render_artifact_morph([raw_img, mask_img, cam_img], ...) ➔ .mp4 │
│   • visual_kit.render_3d_surface_orbit(surface_type, elevation, ...)   ➔ .mp4 │
│   • visual_kit.render_latent_cluster_orbit(embeddings_3d, labels, ...) ➔ .mp4 │
│   • visual_kit.render_network_flow(stage_nodes, tensor_shapes, ...)   ➔ .mp4 │
│   • visual_kit.render_diagnostic_plot(chart_type, telemetry_data, ...) ➔ .png │
└───────────────────────────────────────┬─────────────────────────────────────────┘
                                        │ Returns local file path (asset.mp4, asset.png)
┌───────────────────────────────────────▼─────────────────────────────────────────┐
│                   TIER 2: Slide Canvas Composition (slide_kit)                  │
│       • Composes native PowerPoint elements at arbitrary (x, y, w, h) coords   │
│                                                                                 │
│   • slide_kit.create_slide(prs, bg_color=Theme.BG_DARK)                         │
│   • slide_kit.add_video(slide, x, y, w, h, video_path, poster_image_path=None) │
│   • slide_kit.add_image(slide, x, y, w, h, image_path, caption=None)           │
│   • slide_kit.add_code_box(slide, x, y, w, h, code, title=None)                │
│   • slide_kit.add_card / add_metric_card / add_callout_banner(...)              │
└─────────────────────────────────────────────────────────────────────────────────┘
```

- `digitalagedu/core/llm/presentation_designer.py`
- `digitalagedu/core/llm/slide_kit.py`
- `digitalagedu/core/llm/context.py`
- `digitalagedu/core/llm/main.py`
- `pyproject.toml`
- Any existing artifact-generation, image-processing, execution-isolation, and presentation-testing utilities.
  Because **Tier 1 only generates media files** and **Tier 2 only positions elements on the slide**, the LLM retains infinite layout flexibility:
- Split-screen (e.g., code left, 3D orbit right).
- Hero visual (e.g., large center artifact morph with KPI metrics beneath).
- Diagnostic comparison (e.g., side-by-side success vs. failure with Grad-CAM wipe).
- Pure conceptual slides (text, cards, tables) when visual movement adds no pedagogical value.

Identify how presentation prompts are constructed, how generated code is executed, how assets are located, how output files are managed, and how the final presentation is returned to the user.
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Preserve existing working behavior and integrations wherever possible. Do not assume the repository's current implementation matches this description exactly; verify the actual code before making changes.

## 2. Animation & Visualization Engine Selection

## 2. Integrate Animation and Visualization Libraries

### A. 3D Scientific & Spatial Dynamics: PyVista & Matplotlib 3D

- **PyVista (Built on VTK)**: High-level Pythonic scientific visualization with native **off-screen headless rendering** (`pv.Plotter(off_screen=True)`). Generates smooth 3D camera orbits around mathematical surfaces and 3D point cloud clusters. Exports to `.mp4` via `ffmpeg` / `imageio`.
- **Matplotlib 3D (`mpl_toolkits.mplot3d` + `FuncAnimation`)**: Zero-dependency built-in option using the headless `Agg` backend. Excellent lightweight fallback for rotating 3D loss valleys and 3D embedding scatters.
- **Why Not Three.js for Slides?** PowerPoint does not support embedded WebGL or client-side JavaScript. Capturing Three.js into video requires running a headless browser (Puppeteer/Node.js) on HPC nodes, which is fragile and resource-heavy. **Three.js is reserved solely for optional interactive web widgets in the React portal**, whereas slides rely on Python-native MP4/GIF generation.

Evaluate and integrate the smallest practical set of libraries that provides the required capabilities.

### B. 2D Conceptual & Algorithmic Animations: Manim Community

- **Use Cases**: Neural network layer forward passes, attention matrix heatmaps, tensor reshaping, gradient descent step progression.
- **Declarative Primitives**: Provide pre-built, parameterized Manim scene primitives (`NetworkFlowScene`, `AttentionHeatmapScene`, `TensorTransformScene`) rather than prompting the LLM for arbitrary unconstrained Manim scripts.
- **Graceful Fallback**: If `manim` or system C-libraries (`cairo`, `pango`) are unavailable in the runtime environment, the engine automatically degrades to static vector diagrams or Matplotlib figures.

### Required: Manim Community

### C. Authentic Artifact Sequencing: Pillow + ImageIO

- **Use Cases**: Smoothly animating real computational pipeline fixtures:
  - Raw Input Image $\rightarrow$ SAM Segmentation Mask $\rightarrow$ Grad-CAM Heatmap overlay.
  - Side-by-side sliding wipe between ground truth and mispredicted edge cases.
- **Strengths**: 100% headless, zero risk of C-compilation failures, fast rendering (< 1s), and produces loopable animated GIFs or MP4s that autoplay inside PowerPoint.

Use Manim as the primary engine for programmatically generated educational animations.

### D. Data-Driven Diagnostic Figures: Matplotlib & Plotly

- **Use Cases**: Empirical confusion matrices, class distribution histograms, ROC curves, training epoch convergence.
- **Empirical Grounding**: Charts must strictly pull from actual pipeline telemetry (`results.csv`, `run_summary`). Never fabricate data. If data is absent, the LLM omits the chart or labels it as illustrative.
- **Formats**: Static high-res PNG for PPTX embedding; optional interactive JSON/HTML export for the web portal.

It should support concepts such as:
-----------------------------------

- Neural network architecture and forward propagation.
- Attention mechanisms and transformer components.
- Gradient descent and optimization.
- Matrix operations, embeddings, and tensor transformations.
- Algorithms and computational workflows.
- Computer vision pipelines and model inference.
- Step-by-step explanations of scientific and mathematical concepts.

## 3. Extending `slide_kit.py` & Introducing `visual_kit`

The LLM should be able to describe an animation's educational purpose, visual elements, sequence of events, labels, timing, and emphasis. A rendering layer should translate that description into an animation.

### A. `digitalagedu/core/llm/visuals/visual_kit.py`

Exposes domain-agnostic asset generators:

- `render_artifact_morph(image_paths: List[str], captions: List[str], duration_per_frame: float = 1.5, output_dir: str = ...) -> str`
- `render_3d_surface_orbit(surface_type: str = "loss_landscape", elev: float = 30, frames: int = 60, output_dir: str = ...) -> str`
- `render_latent_cluster_orbit(points_3d: np.ndarray, labels: List[str], output_dir: str = ...) -> str`
- `render_network_flow(stages: List[str], highlight_idx: Optional[int] = None, output_dir: str = ...) -> str`
- `render_diagnostic_plot(chart_type: str, data: Dict[str, Any], output_dir: str = ...) -> str`

Prefer a structured animation specification and a collection of reusable scene primitives over unrestricted execution of arbitrary model-generated Python. The system should still permit meaningful variation and composition rather than limiting the model to a handful of fixed scenes.

### B. `digitalagedu/core/llm/slide_kit.py` Extensions

Adds shape placement primitives to PowerPoint slides:

- `slide_kit.add_video(slide, x, y, w, h, video_path: str, poster_image_path: Optional[str] = None)`: Uses `slide.shapes.add_movie(...)` with H.264 MP4 and a first-frame poster image to prevent black screens.
- `slide_kit.add_image(slide, x, y, w, h, image_path: str, caption: Optional[str] = None)`: Uses `slide.shapes.add_picture(...)` with aspect ratio preservation and optional bottom caption card.
- `slide_kit.add_artifact_comparison(slide, x, y, w, h, original_path: str, processed_path: str, labels: Tuple[str, str])`: Side-by-side image comparison with styled metadata badges.

Render animations into media formats suitable for embedding in presentations, preferably MP4 where supported, with GIF or static-image fallbacks when appropriate.
------------------------------------------------------------------------------------------------------------------------------------------------------------------

### Recommended: Plotly and Matplotlib

## 4. Presentation Prompt Engineering

Use Plotly for data-driven visualizations, including animated charts and 3D plots where useful. Use Matplotlib for scientific plots, static figures, and additional rendering capabilities.
Update `CONCEPT_SLIDE_BUILDER_SYSTEM` / `build_concept_slide_prompt` in `presentation_prompts.py` to document the Two-Tier Toolkit.

Visualizations must use actual pipeline telemetry, model outputs, datasets, or explicitly supplied example data. Never fabricate accuracy, AUC, dataset sizes, experimental outcomes, or other scientific results to make slides look more impressive.
The prompt instructs the model to:

1. **Analyze Pedagogical Purpose**: Does this concept require temporal motion (animation), geometric spatial intuition (3D orbit), empirical validation (chart), or reference implementation (code)?
2. **Select the Right Medium**:
   - Use `visual_kit.render_artifact_morph` for computer vision pipeline transformations (raw $\rightarrow$ mask $\rightarrow$ Grad-CAM).
   - Use `visual_kit.render_3d_surface_orbit` for optimization concepts, loss landscapes, and spatial manifolds.
   - Use `visual_kit.render_network_flow` for deep learning layer architectures and tensor dimensions.
   - Use `visual_kit.render_diagnostic_plot` for confusion matrices and class distributions.
   - Use `slide_kit.add_code_box` alongside visuals for implementation mechanics.
3. **Compose Unconstrained Layouts**: Combine primitives freely using `(x, y, w, h)` coordinates within the 16:9 canvas (13.333" $\times$ 7.5"). Avoid repetitive slide structures across the deck.
4. **Enforce Evidence Grounding**: Anchor claims and charts directly to the provided `telemetry` dictionary.

If data is missing, the LLM must omit the visualization, use a clearly labeled illustrative example, or explain that the information is unavailable.
----------------------------------------------------------------------------------------------------------------------------------------------------

### Optional: Pillow

## 5. Security, Isolation & Pipeline Integration

Use Pillow for image processing, cropping, compositing, annotation, and creating visual comparisons from actual computational artifacts.

1. **Subprocess Sandboxing for Presentation Execution**:
   - Replace the current in-process `exec()` in `presentation_designer.py` with an isolated runner mirroring `sandbox.py`.
   - Run the presentation code in a separate subprocess with a strict execution timeout (e.g., 90 seconds) and working directory isolation.
   - Catch segfaults, out-of-memory errors, and infinite loops without crashing the main orchestrator process.
2. **Content-Hashed Asset Caching**:
   - Generate SHA-256 hashes of visual generator arguments and input data.
   - Reuse existing rendered `.mp4`/`.png` files across repeated runs or module iterations to avoid expensive re-rendering.
3. **Payload Unification**:
   - Ensure `build_presentation_payload` in `context.py` produces the exact single source of truth passed to both `presentation_designer.py` and saved to `*_slides_payload.json`.
4. **Graceful Fallbacks**:
   - If a video fails to render or a dependency is missing, automatically substitute a static poster frame or diagnostic card and log a warning without aborting presentation generation.
   - Maintain the default fallback deck (`_build_default_presentation`) as a guaranteed safety net.

Examples include:
-----------------

- Original image versus model prediction.
- Original image versus segmentation mask.
- Grad-CAM overlays.
- Side-by-side successful and failed predictions.
- Annotated images with labels and explanatory callouts.

## 6. Implementation Roadmap

### Optional future extension: Three.js

Do not introduce a separate JavaScript rendering service unless it is justified by a concrete requirement. Keep interactive 3D as a potential future extension or companion HTML output.

Avoid unnecessary dependencies and large installations. Check which libraries are already present in the environment and make optional features fail gracefully when their dependencies are unavailable.

## 3. Extend `slide_kit.py` with Composable Visual Capabilities

Add reusable utilities that the LLM can call when composing slides. Depending on the existing architecture, consider capabilities such as:

- Adding images with configurable cropping, positioning, scaling, and captions.
- Creating annotated image comparisons and overlays.
- Generating charts from validated data.
- Creating custom diagrams and process visualizations.
- Rendering and embedding Manim animations.
- Adding callouts, labels, highlights, and explanatory annotations.
- Displaying code alongside corresponding visual explanations.
- Managing media sizing, aspect ratios, and consistent visual quality.
- Handling missing assets and rendering failures gracefully.

Do not implement every capability as a fixed slide layout. Prefer small composable primitives that allow the LLM to design different layouts for different learning objectives.

The LLM should be able to combine text, images, charts, diagrams, animations, code, and whitespace as appropriate.

Maintain a consistent professional visual language, but allow the model to make context-sensitive decisions about colors, layouts, visual hierarchy, and slide density.

## 4. Update the Presentation-Generation Prompt

Update the prompt in `PresentationDesigner` so the model understands its expanded visual capabilities.

The prompt should instruct the model to:

1. Identify the primary learning objective of each slide.
2. Choose the most effective medium for teaching that objective.
3. Prefer meaningful visuals over decorative graphics.
4. Use animation when temporal progression, transformations, or cause-and-effect relationships improve understanding.
5. Use charts when quantitative evidence matters.
6. Use real computational artifacts when they help learners connect concepts to actual research or workflows.
7. Use images, diagrams, annotated comparisons, and code excerpts where educationally appropriate.
8. Include appropriate explanations, labels, captions, and learner-facing questions.
9. Avoid unnecessary animation, visual clutter, repetitive layouts, and text-heavy slides.
10. Adapt slide count and structure to the content rather than following a rigid template.
11. Ensure technical explanations and scientific claims are supported by available evidence.
12. Provide static fallbacks when animations cannot be rendered or embedded.

The model should retain discretion over slide order, composition, visual selection, animation use, and the amount of explanatory detail. Do not force every deck to include an animation or require every slide to follow the same structure.

## 5. Connect the Animation Tools to the Existing Pipeline

Integrate the new capabilities into the existing presentation-generation workflow.

The intended flow is:

1. Existing curriculum agents generate the learning content and computational artifacts.
2. The presentation system gathers the relevant educational content, validated telemetry, solution code, images, and artifact references.
3. The LLM determines the presentation structure and chooses appropriate visual media.
4. Animation and visualization specifications are rendered through the appropriate utilities.
5. The presentation designer composes the resulting assets into the PowerPoint deck.
6. The system validates the deck and reports any failed or unavailable media.

Resolve any existing inconsistency between the presentation payload built by `context.py`, the saved payload JSON, and the data actually supplied to `PresentationDesigner`. Establish a consistent source of truth so the model receives the intended educational content and artifact metadata.

Ensure asset paths are resolved correctly, output files are organized predictably, and temporary rendering files are cleaned up without deleting assets required by the final deck.

## 6. Security, Reliability, and Performance

Treat generated presentation code and animation specifications as untrusted input.

- Do not execute unrestricted LLM-generated Python in the main backend process.
- Run rendering in a restricted subprocess or isolated worker with timeouts and resource limits.
- Restrict filesystem access and disable network access for rendering unless explicitly required.
- Validate animation specifications and permitted rendering operations.
- Prevent generated code from accessing credentials, environment secrets, or unrelated project files.
- Limit animation duration, resolution, frame rate, and resource consumption.
- Cache rendered assets using a stable hash of the validated specification and its relevant inputs.
- Avoid rerendering identical animations unnecessarily.
- Avoid complex fallback deck hierarchies (no mock or stub fallbacks). If presentation generation fails, log the full error diagnostics and exit cleanly without crashing the main pipeline.
- Make rendering failures and errors explicit in logs.

## 7. Educational Quality and Visual Validation

Add validation that checks more than whether the PPTX file was successfully created.

Where practical, verify:

- Required learning objectives are covered.
- Technical claims and metrics match the supplied evidence.
- Media assets exist and are successfully rendered.
- Images and videos fit within slide boundaries.
- Text and visual elements do not overlap unintentionally.
- Animations have appropriate duration and readable labels.
- Every visual supports a learning objective.
- Slides remain understandable if animation playback is unavailable.
- The deck remains visually coherent without forcing all slides into one template.

If feasible within the current stack, render the finished PPTX to slide images for visual inspection or automated layout checks. Reuse available tools before introducing additional infrastructure.

## 8. Testing

Add tests covering:

- Valid and invalid animation specifications.
- Successful Manim rendering.
- Embedding rendered animation media into a PowerPoint deck.
- Chart generation using real telemetry.
- Image processing and artifact handling.
- Missing optional dependencies.
- Rendering timeouts and failures.
- Static fallback behavior.
- Caching and temporary-file cleanup.
- End-to-end generation of a sample deck.

Include at least one representative example that demonstrates how the LLM can select and combine different visual types for a lesson without following a fixed slide template.

## 9. Deliverables

Implement the changes directly in the repository and provide:

1. A concise explanation of the existing architecture and the modifications made.
2. The libraries selected and the rationale for each.
3. The updated presentation-generation prompt and visual tool interfaces.
4. Dependency and environment setup changes.
5. Tests and their results.
6. Instructions for running the new functionality in the existing pipeline.
7. Any known limitations, especially PowerPoint animation playback compatibility.
8. A sample generated presentation or a representative test output, if the environment permits.

## Constraints

- Preserve the existing Python backend and vLLM integration.
- Preserve the current LLM-directed, open-ended slide composition approach.
- Do not replace the pipeline with a JavaScript-first presentation framework.
- Do not hardcode a universal slide template or require animations on every slide.
- Do not fabricate scientific evidence or use generated decorative imagery in place of actual computational results.
- Avoid unnecessary architectural rewrites.
- Inspect before modifying, implement incrementally, and verify the result with tests.

**Success criterion:** Given different learning objectives and available computational artifacts, the LLM can independently produce visually distinct, educationally effective presentations that combine native PowerPoint elements with relevant custom animations and scientific visualizations, while remaining secure, reproducible, and integrated into the existing pipeline.

```
┌────────────────────────────────────────────────────────────────────────┐
│  Phase 1: Visual Asset Engine (digitalagedu/core/llm/visuals/)         │
│  • Implement Pillow/ImageIO artifact cross-dissolve & morph engine     │
│  • Implement Matplotlib 3D & PyVista headless orbit renderer           │
│  • Implement Manim declarative network/attention scene renderer        │
│  • Implement telemetry-grounded diagnostic chart generator             │
│  • Implement SHA-256 asset caching and headless safety flags           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│  Phase 2: slide_kit.py & Subprocess Sandbox Hardening                 │
│  • Add slide_kit.add_video (MP4 + poster frame extraction)             │
│  • Add slide_kit.add_image and add_artifact_comparison                │
│  • Refactor PresentationDesigner to execute scripts in a subprocess    │
│  • Unify presentation payload between context.py and main.py           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│  Phase 3: Prompt Update & Agent Integration                            │
│  • Update PresentationCodeSchema and designer system prompts           │
│  • Inject visual_kit APIs, telemetry fixtures, and composition rules   │
│  • Validate self-healing retry loop with visual execution errors       │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│  Phase 4: Verification & Test Suite                                    │
│  • Unit tests for visual generators (mocked & real rendering)          │
│  • Test missing dependency fallbacks (graceful degradation)            │
│  • End-to-end presentation generation test asserting 16:9 bounds       │
│  • Verify PPTX media embedding and playback compatibility              │
└────────────────────────────────────────────────────────────────────────┘
```
