# Changelog

All notable changes to the **DigitalAgEdu Curriculum Generator** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-08-17

### Added
- **Foundation Vision Pipeline**:
  - Integrated **DINOv2** (Vision Transformer ViT-B/14) for self-supervised feature extraction and zero-shot/transfer image classification.
  - Integrated **Segment Anything Model (SAM)** for automated and prompt-guided region-of-interest segmentation.
  - Integrated **Phi-3-Vision** (128k context) for multimodal visual question answering and dataset diagnostic reporting.
  - Integrated **Grad-CAM** saliency maps for explainable AI (XAI) feature attribution.
- **Templated Curriculum & Practice Generation Engine**:
  - Built `PracticeGenerator` and `Renderer` in `digitalagedu/core/` driven by modular Jinja2 templates (`digitalagedu/templates/`).
  - Dynamic generation of scaffolded student exercises (`_exercise.py`), instructor reference solutions (`_solution.py`), and automated pytest test suites (`_test.py`).
  - Synthesis of theoretical overviews (`concepts.md`) and curated learning resources (`resource.md`).
  - Automatic module folder hierarchy organizing generated assignments into structured `Week_XX/{module_name}/` directories.
- **Telemetry & Evaluation**:
  - Automated extraction of class distribution statistics, confusion matrices, precision/recall metrics, and IoU segmentation scores.
  - Dynamic injection of live dataset metrics into student assignment docstrings and unit tests.
  - **Weights & Biases (W&B)** telemetry tracking for multi-fold training and validation runs.
- **HPC & Container Infrastructure**:
  - Slurm batch execution scripts for **Ohio Supercomputer Center (OSC)** clusters: `cluster_jobs/run_cardinal.sh`, `cluster_jobs/run_skin_cancer.sh`, and `cluster_jobs/run_hurricane.sh`.
  - Kubernetes job manifests (`configs/job.yaml`, `configs/pvc.yaml`) for deployment on the **National Research Platform (NRP Nautilus)**.
  - Unified, system-agnostic container execution via `Dockerfile` and `entrypoint.sh`.
  - Tapis v3 application specification (`app.json`) and TAP component metadata (`component.yaml`).
- **Domain Configurations**:
  - Sample multi-week domain configurations for Skin Cancer classification (`configs/skin_cancer_config.yaml`), Food classification (`configs/food_config.yaml`), and Hurricane cyclone tracking (`configs/hurricane_config.yaml`).
- **Documentation**:
  - Step-by-step deployment guide (`documentation/HOW_TO_USE.md`).
  - Comprehensive YAML configuration reference (`documentation/YAML_CONFIG_GUIDE.md`).
  - Developer sprint progress logs (`sprints/sprint_one.md`, `sprints/sprint_two.md`, `sprints/sprint_three.md`).

### Known Limitations
- Dataset root paths containing spaces or special symbols (e.g. parentheses) may cause the scanner to fail; clean paths required.
- `max_samples` YAML configuration limits exploratory metric calculation but does not truncate full model training loops.
- In `image_datasets`, `label_idx` variable scoping in select multi-label branch contexts requires verification.
- In `gradio_deployment`, output tensor mapping for `probs` requires explicit multi-class shape handling in standalone deployment stubs.
