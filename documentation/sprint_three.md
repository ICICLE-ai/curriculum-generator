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
