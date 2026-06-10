# Sprint Two - Performance & Validation

## 06/03/2026

The primary goal today was to migrate the pipeline to the OSC Ascend cluster, radically improve inference speed via batched dataloaders and `flash_attention_2`, and restructure the pipeline to ensure mathematical robustness and Explainable AI (XAI).

| Component | What | Why |
| :--- | :--- | :--- |
| **Batched Inference** | Refactored `run_pipeline` to process data in chunks using PyTorch `DataLoader`. | Replaced the slow sequential image-by-image loop, allowing the GPU to process multiple inputs simultaneously. |
| **Flash Attention** | Upgraded Phi-3-Vision to use `flash_attention_2`. | Drastically accelerated VRAM utilization and transformer processing speed on the cluster. |
| **Explainable AI (XAI)** | Removed the "Anchoring Bias" by decoupling DINOv2 and VLM prompts. | The VLM now acts as a diagnostic explainer instead of a binary classifier, generating rich justifications for DINO's outputs. |
| **Metrics Refactoring** | Created `metrics.py` to calculate Precision, Recall, and F1 Scores per class. | Provides deeper mathematical validation of model performance beyond raw accuracy, specifically for imbalanced datasets. |
| **Early Stopping** | Implemented Validation Tracking and In-Memory Checkpointing in Week 8. | Prevents DINOv2 from overfitting during fine-tuning by automatically saving the model state at its peak validation performance. |

### Other Updates

* Created a dedicated `cluster_jobs/` folder containing dataset-specific bash scripts (`run_skin_cancer.sh`, `run_hurricane.sh`) for easier OSC submissions.
* Successfully processed 1,000-image datasets in under 1 hour each, achieving 94.5% accuracy on Hurricane Damage and 86.2% on Skin Cancer.

## 06/04/2026

The primary goal today was to implement advanced model validation techniques to ensure absolute reproducibility and combat overfitting, shifting the focus from pipeline execution to scientific dependability.

| Component | What | Why |
| :--- | :--- | :--- |
| **Stratified 5-Fold CV** | Replaced the physical `train`/`test` folders with dynamic, in-memory Stratified K-Fold splits in `week_08/solution.py`. | Ensures models are rigorously evaluated across all data subsets, proving stability and eliminating "lucky" random splits. |
| **Pipeline Reproducibility** | Upgraded the YAML schema to accept a global `seed` and pushed it to Python, Numpy, and PyTorch. | Locks the entire pipeline’s randomness (from dataloading to weight initialization) to guarantee 100% reproducible results. |
| **Metadata Tracking** | Intercepted the master seed and logged it into `run_summary.json`. | Satisfies the requirement to track run metadata, making every execution auditable and defensible. |

## 06/05/2026

The primary goal today was to finalize the research deliverables by implementing advanced HPC optimizations to prevent hardware starvation and deploying a formal mathematical evaluation package for downstream analysis.

| Component | What | Why |
| :--- | :--- | :--- |
| **HPC DataLoader Optimization** | Increased PyTorch `DataLoader` workers (`num_workers=8`) and enabled `pin_memory`. | Resolved severe CPU bottlenecks (97% idle time) by parallelizing image processing, allowing the GPU to hit near-maximum utilization on the OSC cluster. |
| **Dual Confusion Matrices** | Generated both a Global 5-Fold Validation Matrix and a Final Evaluation Matrix using Seaborn. | Definitively proves that the underlying training architecture is stable across all data (Validation) and accurately generalizes to hold-out datasets in production (Evaluation). |
| **Pipeline Stage Runtimes** | Implemented a linear tracking dictionary to measure execution time per pipeline stage. | Provides deep visibility into architectural bottlenecks, accurately logging the time spent on Classification vs. Segmentation vs. VisionQA. |
| **Medical Error Analysis** | Explicitly tracked and reported False-Negative Rates (Sensitivity) for the Skin Cancer task. | Contextualizes raw accuracy for the medical domain, proving the model successfully catches ~88% of malignant lesions. |

## 06/09/2026

The primary goal today was to finalize the research documentation for HPC deployment and implement advanced clinical metrics to satisfy medical diagnostic reporting standards.

| Component | What | Why |
| :--- | :--- | :--- |
| **Clinical Metrics** | Added `specificity`, `false_negative_rate`, and `false_positive_rate` to the core evaluation output. | Satisfies rigorous medical research requirements by providing a granular breakdown of diagnostic errors beyond raw accuracy. |
| **AUC-ROC Implementation** | Refactored the classification stage to output `softmax` probabilities and calculated the true AUC-ROC score using `scikit-learn`. | Essential for evaluating the model's ability to distinguish between benign and malignant classes at various thresholds. |
| **Tapis/HPC Boilerplate** | Created a standardized `sample_config.yaml` boilerplate template with explicit dataset and model pathing rules. | Ensures future researchers can reliably deploy the pipeline on the OSC cluster without downloading gigabytes of models locally by utilizing persistent shared storage. |
| **Documentation Structuring** | Drafted comprehensive "Deployment and Reproducibility" documentation and clarified XAI claims. | Makes the codebase defensible in an academic setting and prepares the project for containerized batch job deployment. |

## 06/10/2026

The primary goal today was to engineer a robust, containerized deployment architecture for Tapis integration and resolve edge-case metric calculation bugs.

| Component | What | Why |
| :--- | :--- | :--- |
| **Metric Robustness** | Patched an indexing conflict within `metrics.py` between PyTorch and `scikit-learn` for binary AUC-ROC calculations. | Ensures the pipeline accurately calculates evaluation metrics regardless of whether the target dataset is binary or multi-class, without throwing dimension errors. |
| **Containerization** | Developed a `Dockerfile` utilizing PyTorch's `devel` base image to compile `flash-attn` from source. | Freezes the exact pipeline environment (CUDA, PyTorch, Python 3.10) into a portable image, completely eliminating the "it works on my machine" problem for future researchers. |
| **Tapis Architecture** | Configured `app.json` and an `entrypoint.sh` wrapper script mapped to OSC's persistent storage. | Abstracts away manual SSH/SLURM commands, allowing users to submit massive batch jobs to the supercomputer entirely through the Tapis web portal. |
| **CI/CD Pipeline** | Implemented a GitHub Actions workflow (`docker-build.yml`) using GitHub SSO authentication. | Automates the Docker build process in the cloud, completely bypassing local hardware storage limitations and pushing the production-ready image straight to Docker Hub. |
