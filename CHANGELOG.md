# Changelog

All notable changes to the **Smart Curriculum Designer** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-10-07

### Added
- **Multi-Agent Curriculum Synthesis Engine**:
  - Replaced static Jinja2 template generation with an autonomous multi-agent pipeline (`Syllabus Architect`, `Problem Formulation Agent`, `Solution Engineer`, `QA Verification Agent`, and `Presentation Designer`).
  - **Autonomous Syllabus Planning**: Automatically synthesizes multi-week pedagogical curricula and progression milestones calibrated to target grade levels and grounded in Phase 1 dataset profiling.
  - **Sandboxed Test-Driven Synthesis (TDD)**: Generates reference solutions, validates executable correctness via subprocess unit tests with automated self-healing retries, and scaffolds starter code skeletons directly from verified implementations.
  - **Agentic Presentation Generation**: Synthesizes 16:9 widescreen presentation slide decks (`.pptx`) for each module, combining domain challenge directives, modular code architecture, telemetry metrics, and diagnostic error cases.
  - **Domain RAG Grounding**: Integrated vector retrieval (Qdrant) and cross-encoder reranking to ground generated exercises and materials in domain knowledge.
- **Full-Stack Web Portal & Configuration Designer**:
  - Interactive React + TypeScript single-page application for educators to configure domain courses, customize weekly modules, and inspect generated YAML specifications.
  - Pre-packaged curriculum presets for agriculture/plant pathology, healthcare/dermatology, and food analytics.
  - Multi-source dataset ingestion supporting client-side archive extraction (`.zip`, `.tar`, `.tar.gz`), remote URL transfers, and cluster file selection.
- **Tapis v3 Integration & HPC Job Execution**:
  - End-to-end integration with Tapis v3 services (authentication, compute jobs, files, and server-side data transfers).
  - Streamlined cluster job submission abstracting Slurm options, GPU allocation, and compute resources.
  - Automated Singularity/Apptainer scratch cache redirection to prevent cluster home directory quota exhaustion.
  - Interactive job monitor with real-time pipeline telemetry and an interactive file explorer to navigate, preview, and download job deliverables.
- **Documentation**:
  - Comprehensive user portal walkthrough in `documentation/HOW_TO_USE.md` with step-by-step screenshots covering login, configuration, cluster job submission, and deliverable inspection.

### Changed
- Shifted curriculum practice generation from static code templates to dynamic LLM agent workflows grounded in live computer vision pipeline metrics and dataset telemetry.
- Refactored frontend and service layers into modular, decoupled components.

---

## [0.1.0] - 2026-08-17

### Added
- **Foundation Vision Pipeline**:
  - Integrated **DINOv2** (Vision Transformer ViT-B/14) for self-supervised feature extraction and zero-shot/transfer image classification.
  - Integrated **Segment Anything Model (SAM)** for automated and prompt-guided region-of-interest segmentation.
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
