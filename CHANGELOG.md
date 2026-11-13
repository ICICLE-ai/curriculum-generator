# Changelog

All notable changes to the **Smart Curriculum Designer** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-13

### Added

- **AI lesson generation on the National Research Platform.** Lessons, code and slides are now written by models on NRP's AI service instead of a model loaded onto the job's GPU. The project provides access through its own AI service, so you do not need an NRP key: jobs sign in with your Tapis login.
- **AI Lesson Writer Models** in **Lab Settings**: choose which AI model plans the course, writes the code, arbitrates failing tests, builds the slides and reviews them.
- **Independent Arbiter.** When generated tests and solutions keep disagreeing, an AI from a different model family decides which side is wrong and directs the fix. If the week's specification itself is at fault, it is rewritten and the week is rebuilt.
- **Screenshot review of every slide.** Each slide is rendered and checked by a vision-capable AI for overlapping, cut-off or unclear content before it is kept. Crowded slides are split in two instead of having content cut.
- **Lesson-style slide decks.** Each week's deck follows a teaching order (goal → overview → method → why → application → key takeaways), with speaker notes, and charts drawn only from your run's real data.
- **Generation trace for every week** (`{module}_generation_trace.json` and `trace/`): a verifiable record of every AI request, code version, test run and repair behind the week's materials.
- **Week build logs** (`{module}_phase2.log`) in each week's folder.

### Changed

- **Weeks are built in parallel**, up to four at a time, once each week's problem statement is written. A 4-week course now takes about 3.5–4.5 hours of run time (plus queue wait), instead of building each week after the previous one finished.
- **Weeks build on each other.** Each week's problem statement now sees what earlier weeks covered, so it builds on prior work instead of repeating it.
- **One failed week no longer stops the course.** The remaining weeks finish, and the job reports which week failed. A week whose code cannot pass its tests gets no starter code or slides.

### Known issues

- **Shared AI capacity.** All portal users share the project's AI access, with a limit on how many requests run at once, so courses take longer when many are being built at the same time.

---

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
