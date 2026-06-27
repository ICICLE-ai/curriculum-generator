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
| **CI/CD Pipeline** | Implemented a GitHub Actions workflow (`docker-build.yml`) using GitHub SSO authentication and Docker layer caching. | Automates the Docker build process in the cloud, completely bypassing local hardware storage limitations and pushing the production-ready image straight to Docker Hub. |
| **Cloud Deployment** | Successfully registered the `digital-age-edu` application to the ICICLE Tapis tenant via the REST API. | The pipeline is now officially live. Researchers no longer need to manually SSH into the OSC cluster, write SLURM `.sbatch` scripts, or handle terminal execution. The entire pipeline can now be triggered dynamically from a web browser via the Tapis UI. |

## 06/11/2026

The primary goal today was to resolve isolated container filesystem bugs and bridge the authorization gap between the Tapis Security Kernel and the OSC cluster.

| Component | What | Why |
| :--- | :--- | :--- |
| **Container File Routing** | Refactored output paths to dynamically map to `_tapisExecSystemOutputDir` via environment variables. | Singularity containers are strictly read-only. This prevents `OSError: [Errno 30]` crashes by correctly routing generated masks and CSV outputs into Tapis' temporary `harvest_jobs` scratch space. |
| **Direct SSH Authentication** | Generated an unencrypted PEM RSA key and manually uploaded the public footprint to the Tapis PKI system. | Bypasses the highly restricted `ascend-static` proxy account, allowing the pipeline to natively submit jobs using the researcher's absolute identity and permissions. |
| **SLURM Injection** | Injected `-A PAS2699` via the `schedulerOptions` array within the Tapis `app.json`. | Satisfies the strict OSC billing requirements; without it, the supercomputer instantly rejects the `sbatch` submission script. |

## 06/12/2026

The primary goal today was to eliminate headless container crashes, explicitly bind supercomputer hardware via Tapis parameters, and prevent catastrophic storage bloat.

| Component | What | Why |
| :--- | :--- | :--- |
| **Headless OpenCV Fix** | Replaced `opencv-python` with `opencv-python-headless` in the core dependencies. | Standard OpenCV searches for `libGL` graphical pop-up libraries that do not exist on headless supercomputers, causing instant import crashes. The headless version is pre-compiled for pure server environments. |
| **NVIDIA Driver Binding** | Mapped `--nv` via `containerArgs` and `--gpus-per-node=1` via `schedulerOptions` in `app.json`. | The `nextgen` queue refuses to allocate GPUs without explicit requests. Furthermore, Singularity containers are "blind" and will crash via `RuntimeError: Found no NVIDIA driver` unless explicitly told to bind the host system's graphical compute units. |
| **DataLoader CPU Starvation** | Scaled the Tapis `coresPerNode` parameter from `1` to `12`. | The PyTorch multiprocessing data loader (`num_workers=8`) was suffering severe GIL contention on a single core, grinding inference to a crawl. Assigning 12 cores returned the execution time from 5+ hours back to a nominal 3 hours. |
| **Scratch Space Caching** | Rerouted `HF_HOME`, `TORCH_HOME`, and `APPTAINER_CACHEDIR` to the 100TB project drive via Tapis `envVariables`. | By default, Tapis re-downloads massive 9GB container layers and multi-gigabyte models to the local home directory on every iteration, which would rapidly crash the strict 500GB OSC quota limit. |

## 6/26/2026

The primary goal today was to prove the pipeline is completely cluster-agnostic, allowing seamless Tapis job submissions across all three ICICLE clusters (Ascend, Cardinal, and Pitzer) using a single, unified Docker image.

| Component | What | Why |
| :--- | :--- | :--- |
| **Cluster Generalization** | Refactored `app.json` to remove hardcoded `cpu-request` and added a dynamic `cluster-request` flag set to `INCLUDE_BY_DEFAULT`. | Because all OSC clusters share the same login node, SLURM was misrouting Tapis jobs to default partitions. This fix allows researchers to dynamically route jobs to any cluster directly from the job submission payload without ever needing to re-register the Tapis app. |
| **Cardinal SLURM Constraints** | Mapped Cardinal's exact 104-core / 4-GPU H100 topology to Tapis by setting `coresPerNode` to precisely `26`. | Cardinal enforces incredibly strict hardware constraints. Requesting `12` CPUs for `1` GPU resulted in instant `Requested node configuration is not available` SLURM rejections because it stranded the other 14 CPUs sharing that GPU's PCIe lane. |
| **Hardware-Agnostic Attention** | Ripped `flash-attn` out of the Docker dependencies and fell back to PyTorch's native Scaled Dot Product Attention (SDPA). | Flash Attention 2 explicitly dropped support for older Volta (Pitzer) and Pascal (Owens) architectures. By relying on native SDPA, PyTorch now dynamically switches between Flash Attention on Cardinal/Ascend and Memory-Efficient math on Pitzer, avoiding runtime crashes. |
| **Tapis Queue Debugging** | Identified false-positive `FILES_CLIENT_SSH_NOT_FOUND` errors as symptoms of Tapis internal queue backlogs. | Proved that the output directories simply do not exist while a job is stuck in the `PENDING` state; they are only instantiated when Tapis transitions to `STAGING_JOB`. |
