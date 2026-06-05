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
