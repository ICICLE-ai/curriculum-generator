# DigitalAgEdu Release Notes: Primary Release v1.0.0 (Iteration Two)

**Release Date:** August 17, 2026  
**Release Tag:** `v1.0.0`  
**License:** MIT  

---

## Executive Overview

**DigitalAgEdu v1.0.0** is the primary open-source release of the AI-driven automated curriculum generation and computer vision framework. Developed under the NSF ICICLE AI Institute at The Ohio State University, DigitalAgEdu operationalizes the principle that **"the pipeline is the curriculum."**

Rather than assigning artificial toy datasets, the framework executes an end-to-end foundation model computer vision pipeline on authentic scientific and real-world image datasets. The empirical metrics, confusion matrices, class imbalances, and segmentation masks generated during execution are dynamically injected into scaffolded Python exercises, reference solutions, and automated test suites for students.

---

## Key Features & Architecture

### 1. Multi-Model Foundation Vision Pipeline
* **DINOv2 (Vision Transformer):** Leverages self-supervised ViT-B/14 backbones for dense visual feature representation, zero-shot transfer, and robust image classification.
* **Segment Anything Model (SAM):** Computes promptable, zero-shot semantic segmentation masks to isolate regions of interest (e.g., agricultural foliage, melanoma boundaries, satellite storm eyes).
* **Phi-3-Vision (Multimodal VLM):** Provides natural language reasoning and automated visual diagnostic reports grounded in image inputs.
* **Explainable AI (Grad-CAM):** Generates gradient-weighted class activation maps, teaching students how neural network attention corresponds to visual semantics.

### 2. Dynamic Templated Curriculum Engine
* **Jinja2 Master Templates (`digitalagedu/templates/`):** Contains modular assignment templates spanning NumPy, Pandas, PyTorch tensors, custom CNN architectures, transfer learning, semantic segmentation, and Gradio deployment.
* **Scaffolded Student Deliverables:** For every selected module, the engine compiles:
  * `[module]_exercise.py`: Scaffolded student workspace with docstrings, type annotations, and `# TODO` milestones.
  * `[module]_solution.py`: Fully functional instructor reference solution.
  * `[module]_test.py`: Automated pytest test suite validating tensor shapes, algorithmic accuracy, and edge cases.
  * `concepts.md` & `resource.md`: Theoretical explanations and curated reading links.
* **Structured Output Hierarchy:** Synthesized files are automatically organized into clean weekly directories:
  ```
  output/<run_name>/
  └── Week_01/
      └── numpy_basics/
          ├── numpy_basics_exercise.py
          ├── numpy_basics_solution.py
          ├── numpy_basics_test.py
          ├── concepts.md
          └── resource.md
  ```

### 3. Supercomputing (HPC) & Cloud Execution
* **Ohio Supercomputer Center (OSC):** Slurm batch scripts optimized for OSC Cardinal, Ascend, and Pitzer GPU nodes (`cluster_jobs/run_cardinal.sh`, `cluster_jobs/run_skin_cancer.sh`, `cluster_jobs/run_hurricane.sh`).
* **NRP Nautilus:** Kubernetes job manifests (`configs/job.yaml`, `configs/pvc.yaml`) for distributed compute.
* **Containerization:** Unified Docker and Apptainer execution via `Dockerfile` and `entrypoint.sh`.
* **Telemetry & Tracking:** Integrated Weights & Biases (W&B) experiment logging across cross-validation folds.

---

## Quickstart

```bash
# 1. Clone repository
git clone https://github.com/OSU-SAI-Lab/curriculum_generator.git
cd curriculum_generator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run on a cluster
sbatch cluster_jobs/run_skin_cancer.sh
```

---

## Verified Domain Configurations
* **Skin Cancer Classification:** `configs/skin_cancer_config.yaml`
* **Food Classification:** `configs/food_config.yaml`
* **Hurricane Tracking:** `configs/hurricane_config.yaml`

---

## Known Limitations

1. **Filesystem Path Sanitization (Spaces & Special Characters)**:
   * The dataset scanner requires POSIX directory paths without spaces or symbols (e.g., parentheses like `Dataset(Augmented)`). Paths containing spaces or unescaped symbols may cause the scanner to report zero images found. Datasets should be stored in or symlinked to clean paths (e.g., `/fs/ess/PAS2699/.../plant_diseases`).
2. **Dataset Subsampling Scope (`max_samples`)**:
   * The `max_samples` YAML configuration parameter limits exploratory dataset scanning and metrics calculation, but does not currently truncate the full dataset split during model training loops.
3. **HPC Batch Job Progress Visibility**:
   * Training loops output logs at epoch boundaries rather than displaying interactive per-batch progress bars. On massive datasets (>50k images), training may appear quiet in batch `.out` logs between epoch completions.
4. **HPC & Tapis Authentication Prerequisites**:
   * Submitting jobs through Tapis to remote clusters requires pre-configured SSH keys and system credentials. Missing cluster credentials result in `SSH_POOL_MISSING_CREDENTIALS` errors prior to job launch.
5. **Student Starter Code Failing Tests by Design**:
   * Generated student exercise files (`[module]_exercise.py`) contain unimplemented `# TODO` milestones and will intentionally fail unit tests (`[module]_test.py`) until completed by students. Fully passing implementations are provided in `[module]_solution.py`.
6. **Template Variable Scoping**:
   * In `image_datasets`, `label_idx` variable scoping in select multi-label branch contexts requires verification.
   * In `gradio_deployment`, output tensor mapping for `probs` requires explicit multi-class shape handling in standalone deployment stubs.

---

## Institutional Acknowledgements
Supported by the National Science Foundation (NSF) under Award **OAC-2112606 (ICICLE AI Institute)** and developed at **The Ohio State University (Systems and AI Lab)**.
