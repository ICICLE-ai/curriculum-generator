# Sprint Three - Bridging Pipeline & Curriculum Generation

## 06/29/2026

The primary goal today was to bridge the execution of the machine learning pipeline with the curriculum engine, shifting the curriculum generation from a static preview to a dynamic post-run report using live performance metrics.

| Component | What | Why |
| :--- | :--- | :--- |
| **Curriculum Execution Order Shift** | Moved the `CurriculumEngine` generation block in `run_pipeline.py` from the startup phase to the final step of the pipeline execution. | Ensures the generator has access to actual metrics (accuracy, predictions, stage times) computed during the live run. |
| **Post-Run Metrics Ingestion** | Updated `CurriculumService.build()` to accept and process a `pipeline_metrics` dictionary. | Computes overall accuracy, summarizes stage runtimes, and samples real-world correct and misclassified image paths directly from the output results. |
| **Dynamic Syllabus Templates** | Modified `lesson_plan.md.j2` to display live performance metrics and specific image file paths for classroom case studies. | Ground the educator's curriculum in real experimental results and provides immediate visual examples of model successes/failures. |
| **Practice Generator Architecture** | Designed the `PracticeGenerator` to match week-by-week syllabus activities to programming concepts. | Dynamically schedules the correct exercises according to the syllabus, regardless of whether the course is configured for 4, 8, or 16 weeks. |

---

## 06/30/2026

The primary goal today was to author the core programming templates, establish a robust sandboxed verification runner, and resolve environment conflicts on the HPC cluster compute nodes.

| Component | What | Why |
| :--- | :--- | :--- |
| **Core Exercise Templates** | Authored templates for EDA, Preprocessing/Splitting, Baseline Training, and Metrics Evaluation, alongside their matching unit test files. | Provides students with hands-on coding exercises mapped directly to standard PyTorch and OpenCV APIs. |
| **Sandbox Verification Runner** | Implemented `_verify_sandbox` using `tempfile.TemporaryDirectory` and `subprocess` testing. | Automatically validates that all generated reference solutions pass their unit tests (Positive Pass) and starter files fail (Negative Pass) before export. |
| **HPC Python Environment Fix** | Refactored the subprocess command to execute using `sys.executable` instead of `"python"`. | Prevents Windows and cluster nodes from falling back to global system python installations, ensuring tests run in the active virtual environment. |
| **Intel MKL Conflict Resolution** | Copied the OS environment and injected `"MKL_THREADING_LAYER" = "GNU"` before spawning verification subprocesses. | Resolves conflicts between Intel's Math Kernel Library and GNU's OpenMP library on HPC compute nodes, preventing segmentation aborts. |
| **Regex Parser Indentation Fix** | Upgraded the parsing regex in `practice_generator.py` to use `re.MULTILINE` and `^[ \t]*`. | Discards the leading spaces preceding comment tags (`# [REFERENCE_SOLUTION]`), preserving correct Python indentation in exported exercises. |

---

## 07/02/2026

The primary goal today was to scale the curriculum templates database, implement advanced scheduling adaptations, resolve critical verification issues, and expand the data science foundations exercises.

| Component | What | Why |
| :--- | :--- | :--- |
| **All 13 modular templates** | Developed 13 new weekly exercise master templates and matching unit test files. | Provides a comprehensive 6-month visual deep learning curriculum (NumPy, Pandas, PyTorch MLP, OpenCV Segmenter, CNNs, Schedulers, ResNet Transfer Learning, U-Net, Grad-CAM, t-SNE Vector clustering, VLMs, and Gradio portal). |
| **Tiered Complexity Scheduler** | Coded the Tiered Complexity Progression Algorithm in `CurriculumService._generate_activities`. | Automatically filters out advanced deep learning topics for short courses (e.g. 4-week summer camps) and unlocks them sequentially for longer courses (e.g. 24-week AP tracks). |
| **Template-Specific File Exports** | Refactored `PracticeGenerator` to output files as `[template_basename]_exercise.py` instead of generic `exercise.py`. | Prevents files from overwriting each other when a compressed curriculum maps multiple activities to the same week. |
| **Expanded Data Science Foundations** | Fleshed out NumPy and Pandas templates to cover detailed operations (slicing, broadcasting, masks, PCA projection, sorting, groupby aggregation, NaNs, and line/bar/hist/scatter Matplotlib plots). | Elevates the introductory weeks from simple prototypes to rigorous 1-2 hour coding labs. |
| **Verification Patches & Bug Fixes** | Resolved scheduler type checks, banker's rounding checks, VLM prompt assertions, mock model dimensions, and fixed the learning outcomes `UnboundLocalError` week parser crash. | Ensures the entire generator compiles and headlessly validates to 100% success on local systems and HPC compute nodes. |

---

## 07/03/2026

The primary goal today was to enforce complete domain generality across all templates, resolve shape mismatches in deep learning segmentation decoders, and overhaul the scheduling sequence mapping.

| Component | What | Why |
| :--- | :--- | :--- |
| **Domain-Agnostic Generalization** | Generalised VLM prompt templates, Gradio labels, and interactive segmentation window titles (`"OpenCV Segmentation Portal: {{ subject }}"`) to use dynamic Subject configurations instead of hardcoded dermatology/clinical keywords. | Ensures the generated exercises seamlessly fit any custom field (skin lesions, crop health, satellite disaster mapping). |
| **Sequential Weekly Scheduling** | Overwrote the modulo-based activity distribution method in `CurriculumService` with a contiguous chronological chunking algorithm. | Guarantees that activities follow a logical, consecutive learning sequence rather than appearing in scrambled weeks. |
| **Segmentation Decoders Dimension Patch** | Applied bilinear upsampling interpolation inside `semantic_segmentation.py.j2` to scale outputs back to target image dimensions. | Prevents model shape dimension crashes ($518$ vs $516$) when using non-divisible input dimensions. |
| **Datasets & Loaders Foundations** | Developed dataset splits, compose transforms flow tracing, visual batch grids, and conceptual questions in `image_datasets.py.j2`. | Provides students with a robust visual introduction to how image files are structured as tensors. |

---

## 07/04/2026

The primary goal today was to refine visual and architecture-tracing layers in CNN exercises, simplify loader concepts, and establish baseline vs. optimized training loop experiments.

| Component | What | Why |
| :--- | :--- | :--- |
| **Pacing Loader Simplification** | Streamlined `image_datasets.py.j2` to focus exclusively on dataset structures and loading pipelines, stripping out complex systems timing and models loops. | Prevents cognitive overload by introducing one single mental model shift per week. |
| **CNN Visual & Shape Auditing** | Expanded `custom_cnn.py.j2` with step-by-step spatial trace mappings, model summarizers, pooling comparisons, and multi-class activation map plots. | Grayscales and visualizes exactly how convolutions and max pooling layers shrink height/width dimensions. |
| **Optimization Validation Loops** | Implemented `compare_baseline_vs_optimized` in `cnn_optimization.py.j2` to log validation losses and validation accuracies side-by-side. | Demonstrates the stabilizing impact of BatchNorm and Dropout compared to a standard unregularized baseline. |
| **LR & Checkpointing Storytelling** | Plotted step scheduler curves and added terminal logs simulating saving checkpoints and recovering from degraded validation epochs. | Turns abstract optimization features into intuitive, narrative-driven systems workflows. |
| **24-Week Concept Calendar** | Documented the complete 24-week roadmap of weekly objectives inside `templates.md`. | Provides a reference guide mapping the curriculum structure. |
