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

---

## 07/06/2026

The primary goal today was to resolve week alignment offsets, dynamically export curated resource files for each week's directory, and integrate tiered bonus challenges for advanced learners.

| Component | What | Why |
| :--- | :--- | :--- |
| **Week Indexing Realignment** | Merged conceptual introductions directly into the Week 1 NumPy arrays exercise. | Ensures that generated directories align correctly with the academic calendar and coding labs start immediately at Week 1. |
| **Weekly Schedule Markdown Block** | Added a dynamic `Weekly Schedule` block inside `lesson_plan.md.j2` to print out week-by-week activities. | Provides teachers with an instant visual breakdown of student tasks directly in the exported markdown syllabus. |
| **Templated Resource Page Exporter** | Created a generic `resource.md.j2` template and mapped curated documentation links, videos, and articles for all 13 modules in `PracticeGenerator`. | Automatically populates a custom `resource.md` file inside every week's folder, supporting optional independent reading. |
| **Tiered Bonus Challenges** | Implemented advanced optional bonus challenges in NumPy Basics (image patch extraction) and CNN optimization (checkpoint resume checks) with matching unit tests. | Supports tiered difficulty levels, giving fast-paced or CS-experienced students a meaningful learning extension without overwhelming beginners. |
| **Dense Prediction Refactor** | Upgraded Semantic Segmentation week with a "Classification ➔ Dense Prediction" bridge, stable BCEWithLogitsLoss logits output, Soft Dice Loss categorization, and a threshold search bonus challenge. | Resolves loss instabilities, provides logical continuity from classification to pixel-level labels, and teaches post-processing tuning. |
| **Pedagogical Evaluation Report** | Created and detailed weekly exercise strengths, constraints, and actionable fixes inside `tasks/exercise_evaluation.md` using actual pipeline outputs as context. | Provides educators with a comprehensive critique of the curriculum's difficulty pacing, especially for AP CS students. |
| **NumPy Real Image Loader** | Refactored `numpy_basics.py.j2` to load and process raw pipeline output image/mask files using a pre-written PIL helper, supported by a demo `__main__` entry block. | Integrates real-world diagnostic imagery into the first week's matrix calculations instead of using purely mock arrays. |
| **Windows Raw Path Escaping** | Prefixed template-rendered path variables with the Python raw string literal `r` tag. | Resolves path parsing and file loading crashes caused by backslash escape sequences on Windows (e.g. `\benign` parsing as a backspace character). |
| **Unit Test Cheat-Proofing** | Overhauled test templates to assert exact array values, check cross-class indexes, enforce deterministic loss calculations, and run multi-case regex checks. | Blocks student cheating vectors (like returning static placeholders, hardcoded dictionary outputs, or flat matrices) to enforce correct algorithm logic. |
| **Domain-Agnostic Test Compliance** | Cleaned up medical-specific terminology inside the VLM test suites, replacing them with generic visual descriptors. | Ensures the verification harness passes reliably regardless of whether the pipeline runs on medical, agricultural, or other visual domains. |
| **Concept Registry Alignment** | Standardized the registered function name in `concepts_registry.py` to match the template implementation. | Maintained 100% coherence between the core compiler maps and the generated python exercise templates. |

---

## 07/07/2026

The primary goal today was to finalize the pedagogical evaluation and refactor the PyTorch Basics (Week 03-04) template from a tabular dataset to direct image tensor processing, maintaining 100% visual curriculum continuity.

| Component | What | Why |
| :--- | :--- | :--- |
| **PyTorch Basics Image Refactor** | Replaced the tabular Breast Cancer dataset with `SimpleImageMLP` which directly handles flattened grayscale $28 \times 28$ image tensors. | Keeps the entire curriculum 100% aligned with visual computer vision data from start to finish. |
| **Grayscale Image Dataset Loader** | Implemented a robust helper `load_image_dataset` that dynamically downsamples raw dataset directories into standard PyTorch inputs, with automatic random fallback flags. | Ensures robust headless execution regardless of dataset class structures or empty local folders. |
| **Guided Tensor Flattening Task** | Added a batch-safe image flattening step (`torch.flatten(x, start_dim=1)`) as a student TODO inside the forward pass, accompanied by architectural hints. | Teaches students the key structural transition from spatial matrix arrays to fully-connected dense layers while preventing batch-flattening bugs. |
| **Comprehensive Modular Audit** | Added Section 4 to `exercise_evaluation.md` evaluating the helper functions and live pipeline output integrations for all 13 weeks. | Evaluates the structural coherence and real-world authenticity of each exercise module. |
| **PyTorch Dataset OS Whitelist** | Integrated an extension whitelist (`.png`, `.jpg`, `.jpeg`, etc.) inside the `CustomImageDataset` constructor. | Filters out operating system metadata files (like `.DS_Store`) that cause PIL loading failures and runtime crashes. |
| **Windows Raw Path Escaping (Datasets)** | Prefixed `dataset_root` in the visualizer runner block with the Python raw string literal `r` tag. | Avoids Windows backslash escape sequence failures during dataset scanning and visualization. |
| **OpenCV Headless GUI Fallback** | Wrapped OpenCV window loops in Week 5 (Interactive Segmentation) in `try-except cv2.error` blocks. | Avoids window display crashes on headless supercomputers, writing classical floodfill results to `floodfill_demo.png` as a fallback. |
| **CNN Simulated Filter Convergence** | Initialized `conv1` kernels of CustomCNN with Sobel and Laplacian edge filters in the main demo runner. | Solves the con of random noise feature maps, allowing students to study realistic edge activation maps directly on raw pipeline images. |
| **CNN Sample Image Integration** | Upgraded the `__main__` visualizer runner in `custom_cnn.py.j2` to directly load and execute activations on `sample_image_path`. | Bypasses directory-walking errors and guarantees that the model runs directly on the pipeline's output image sample. |
| **CNN Optimization Dataset Loader** | Implemented `load_image_dataset` helper in `cnn_optimization.py.j2` to load actual image dataset splits for baseline vs optimized model validation comparisons. | Provides realistic overfitting and convergence signals on real target images instead of mock noise. |
| **Regularization Weight Histograms** | Implemented a `plot_weight_distributions` function mapping unregularized vs regularized weight parameters. | Solves the dry checkpointing con by visually showing how BatchNorm and Dropout stabilize weight frequencies. |
| **U-Net Shape Verification** | Inserted dimension shape checking assertions inside the decoder forward pass of `semantic_segmentation.py.j2`. | Catches resolution mismatches early, providing clear structural hints on how to align encoder and decoder layers. |
| **U-Net Live Pipeline Runner** | Implemented a complete `__main__` visualizer runner in `semantic_segmentation.py.j2` that processes `sample_image_path` and `sample_mask_path` directly. | Computes combined BCE + Soft Dice Loss on actual SAM target masks, runs threshold tuning searches, and plots comparison grids. |
| **XAI Hook Context Manager** | Abstracted PyTorch hook registration inside a simplified `GradCAMHook` context manager class. | Solves hook complexity and PyTorch deprecation warnings, ensuring automatic hook removal and preventing memory leaks. |
| **XAI Live Pipeline Runner** | Implemented a complete `__main__` visualizer runner in `explainable_ai.py.j2` that processes `sample_image_path` directly. | Generates and overlays class-sensitive Grad-CAM and saliency attention heatmaps on the real image, saving overlays to disk. |
| **Embeddings 2D PCA Clustering** | Implemented a `plot_embedding_clusters` helper rendering 2D scatter coordinates of image features. | Solves high-dimensional vector abstraction by showing students visually how semantic similarities group categories. |
| **Embeddings Live Vector Search** | Implemented a complete `__main__` vector search runner in `vector_embeddings.py.j2` using a self-contained local projection matrix. | Runs nearest-neighbor searches on `sample_image_path` and exports category clusters to `embedding_clusters_pca.png`. |

---

## 07/08/2026

The primary goal today was to support multi-class classification formats in foundations templates, implement independent test-suite execution for students, construct a Pandas tabular demonstration runner, and optimize the curriculum's weekly pacing schedule.

| Component | What | Why |
| :--- | :--- | :--- |
| **Multi-Class PyTorch Basics** | Refactored `calculate_confusion_matrix_manually` in `pytorch_basics.py.j2` and `test_pytorch_basics.py.j2` to construct a 2D tensor matrix. | Enables manual confusion matrix calculation for arbitrary category counts, maintaining print overrides for backward-compatible binary reports. |
| **Independent Student Unit Tests** | Modified the post-export routine in `practice_generator.py` to replace `import target_module` with specific local exercise module aliases. | Allows students to execute unit tests directly in their workspace using standard commands (e.g. `python numpy_basics_test.py`) without file naming errors. |
| **Pandas Data-Audit Demonstration** | Authored the `__main__` visualizer runner in `pandas_analytics.py.j2` to clean NaN logs, calculate accuracies, mine failures, and export Matplotlib charts to disk. | Combines the student's core Pandas data functions into a self-contained local demonstration. |
| **Curriculum Pacing Redistribution** | Modified `curriculum_service.py` to adjust durations of Interactive Image Segmentation (increased to 2 weeks) and Image Embeddings (decreased to 2 weeks). | Evens out the difficulty pacing, giving more time to OpenCV GUI programming and matching Week 5-6 month milestones. |
| **Comprehensive Syllabus Auditing** | Updated `tasks/exercise_method_evaluation.md` to document pipeline parameters, challenge tags `(Challenge)`, provided helper tags `(Provided)`, and week durations. | Delivers a complete, audited reference syllabus of student coding milestones and instructional assets. |

---

## 07/09/2026

The primary goal today was to ensure 100% CWD-independent path portability across all exercises, remove all simulated confidence scoring columns from the Pandas curriculum, dynamically extract unique class categories, and verify execution on the OSC Cardinal cluster compute nodes.

| Component | What | Why |
| :--- | :--- | :--- |
| **CWD-Independent Path Portability** | Refactored `numpy_basics.py.j2`, `pandas_analytics.py.j2`, `transfer_learning.py.j2`, and `semantic_segmentation.py.j2` to resolve data/output paths using `os.path.abspath(os.path.join(os.path.dirname(__file__), ...))`. | Prevents file-not-found exceptions when students run Python scripts and unit tests from different terminal directories. |
| **Confidence-Free Pandas Redesign** | Completely removed all references to synthetic model `confidence` values in `pandas_analytics.py.j2` and `test_pandas_analytics.py.j2`. | Aligns the exercise with authentic pipeline output columns and prevents data/metric fabrication. |
| **Dynamic Class Extraction** | Patched the Pandas audit challenge to read unique categories dynamically using `list(feat_df['ground_truth'].unique())` and raise a `ValueError` if empty. | Resolves a `NameError` crash on real dataset logs and eliminates all hardcoded domain-specific class lists. |
| **OSC Cluster GUI Verification** | Executed and verified the interactive segmentation portal (`Week_05_06`) inside an OSC Open OnDemand Virtual Desktop browser session. | Confirms that classical flood-fill click coordinates and overlays render successfully inside browser VNC sessions on supercomputing nodes. |
| **Cross-Platform Test Mocking** | Added a dynamic mock image generator in `test_numpy_basics.py.j2` when cluster-specific image paths are missing. | Ensures 100% successful compiler verification on local Windows environments without requiring cluster directory mounts. |
