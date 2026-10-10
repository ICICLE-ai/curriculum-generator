# Smart Curriculum Designer

An AI-driven educational framework that integrates automated curriculum generation with an end-to-end computer vision pipeline, enabling learning for high school and undergraduate students combining domain agnostic datasets with machine learning and AI concepts.

### License

[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](./LICENSE) 

**Tags:** `AI4CI`, `CI4AI`, `Foundation-AI`, `Visual-Analytics`

## References

- [Tapis v3 — HPC job execution framework](https://tapis-project.org)
- [DINOv2 — Learning Robust Visual Features without Supervision](https://github.com/facebookresearch/dinov2)
- [Segment Anything (SAM) — Meta AI Foundation Model](https://github.com/facebookresearch/segment-anything)
- [San Diego Supercomputer Center (SDSC Expanse)](https://www.sdsc.edu/support/user_guides/expanse.html)
- [Ohio Supercomputer Center (OSC)](https://www.osc.edu/)
- [ICICLE AI Institute](https://icicle.ai/)

## Acknowledgements
*Developed at The Ohio State University (Systems and AI Lab, advised by Dr. Hari Subramoni), subsequently submitted to and implemented as part of the AI Presidential Challenge, with domain expertise and educator feedback from Dr. Scott Shearer and Dr. Lisa Abrams, and pilot deployment support from the Columbus School for Girls.*

## Issue reporting

Please open an issue at [github.com/ICICLE-ai/curriculum-generator/issues](https://github.com/OSU-SAI-Lab/curriculum_generator/issues) with a description of the problem, steps to reproduce, and any relevant logs from pipeline runs or cluster jobs.

## Tutorials

- **Step-by-Step Tutorials & Deployment:** [HOW_TO_USE.md](./documentation/HOW_TO_USE.md)
- **YAML Configuration Guide & Reference:** [YAML_CONFIG_GUIDE.md](./documentation/YAML_CONFIG_GUIDE.md)
- **Curriculum Module Reference:** [TEMPLATES_GUIDE.md](./documentation/TEMPLATES_GUIDE.md)

---

### Project Philosophy: The Pipeline is the Curriculum

Traditional AI education frequently treats machine learning as a simplified black box using sterile datasets that mask real-world data science challenges. DigitalAgEdu adheres to the principle that **the pipeline itself is the curriculum**. 

Rather than working on generic toy examples, learners execute an end-to-end foundation model pipeline on authentic domain datasets (agriculture, dermatology, disaster response, etc.). The metrics, class imbalances, confusion matrices, and segmentation masks generated during execution are dynamically injected into scaffolded Python exercises. Students dissect, recreate, optimize, and explain the exact stages they just witnessed.

```
       Image Dataset (Any Domain / Kaggle / Tapis)
                          │
                          ▼
    [1] Dataset Ingestion         (Class discovery, validation, sample audits)
                          │
                          ▼
    [2] DINOv2 Classification     (Transfer learning & robust visual representation)
                          │
                          ▼
    [3] SAM Segmentation          (Promptable region-of-interest mask extraction)
                          │
                          ▼
    [4] Grad-CAM Explainability   (Class activation heatmaps & visual evidence)
                          │
                          ▼
    [5] Artifact Packaging        (curriculum.json, syllabus markdown, results.csv, assets)
                          │
                          ▼
    [6] Multi-Agent Synthesis     (Multi-week syllabus & widescreen lecture slides)
                          │
                          ▼
    [7] Exercise Scaffolding      (Scaffolded starter code & PyTorch solutions)
                          │
                          ▼
    [8] Sandboxed Verification    (Property-based unit tests & self-healing loops)
```

### End-to-End Architecture

The DigitalAgEdu architecture consists of decoupled modular systems:

- **Orchestrator & Scanner (`digitalagedu/core/`):** Ingests YAML configurations, parses image directories, computes class distributions, and validates execution readiness.
- **Foundation Vision Pipeline (`curriculum_resources/`):** Houses execution stages for DINOv2 classification (`curriculum_resources/classification/`), SAM segmentation (`curriculum_resources/segmentation/`), and Grad-CAM visual explainability (`curriculum_resources/xai/`).
- **Autonomous Multi-Agent Curriculum Engine (`digitalagedu/core/llm/`):** 3-agent cooperative synthesis pipeline authoring lesson overviews, scaffolded coding exercises, reference solutions, sandboxed unit tests, and lecture slides.
- **Smart Curriculum Designer Web Portal (`frontend/`):** Visual web application delivering interactive pipeline design, 1-click HPC cluster job submission via Tapis v3, and live pipeline stage monitoring.
- **Supercomputing Infrastructure:** Managed job execution on SDSC Expanse with Lustre high-performance scratch storage and Slurm GPU allocation.

### Computer Vision Foundation Models

- **DINOv2 (Vision Transformer Backbone):** Utilizes self-supervised Vision Transformers (ViT) to extract domain-invariant image representations. Enables high classification precision without requiring massive labeled training sets.
- **Segment Anything Model (SAM):** Generates zero-shot promptable segmentation masks to isolate regions of interest (e.g. lesion borders, leaf foliage, flood zones).
- **Grad-CAM (Visual Explainability):** Generates gradient-weighted class activation mapping (CAM) heatmaps to highlight exact visual regions influencing classification decisions, teaching students interpretability and saliency analysis.

### Autonomous Curriculum Generation Process

The generation engine in `digitalagedu/core/llm/` operates via a multi-agent, Test-Driven Development (TDD) workflow that grounds educational content directly in empirical pipeline telemetry:

1. **Telemetry & Provenance Ingestion:** Loads execution telemetry from the computer vision stages (`results.csv`, confusion matrix heatmaps, segmented mask fixtures, class distributions, and runtime performance).
2. **Syllabus Architecture:** When explicit modules are not pre-defined in YAML, the Syllabus Architect agent reviews dataset metadata and performance characteristics to formulate a multi-week academic syllabus (`syllabus_plan.json`, `course_syllabus.md`) with progressive difficulty.
3. **Agent 0 (Problem Formulation & Subsystem Contracts):** Deconstructs each weekly topic into concrete student learning objectives, domain context, and formal subsystem component contracts (`[topic]_overview.md`), linking each topic to verified workflow artifact IDs (`[topic]_manifest.json`).
4. **Agent 2 (Test-First QA Specification):** In accordance with TDD principles, Agent 2 writes property-based unit tests *before* code implementation. The test suite asserts tensor shapes, return types, and algorithmic behavior based on the subsystem contracts (`[topic]_test.py`).
5. **Agent 1 (Reference Solution Synthesis):** Implements the complete PyTorch reference solution designed to pass the unit tests authored by Agent 2 (`[topic]_solution.py`).
6. **Execution Sandbox Verification & Self-Healing:** The synthesized solution and unit tests are executed inside an isolated runtime sandbox (`run_in_sandbox`). If any assertion or syntax error occurs, root-cause diagnosis automatically triggers targeted self-healing retries for either Agent 1 (solution fixes) or Agent 2 (test corrections) until verification succeeds (`[topic]_verification.json`).
7. **Exercise Scaffolding:** From the verified reference solution, student starter code is generated with guided docstrings, `# TODO` implementation milestones, and structural type hints (`[topic]_exercise.py`).
8. **Automated 16:9 Presentation Synthesis:** The Presentation Designer synthesizes structured presentation schemas incorporating pipeline diagrams, evaluation metrics, and theoretical concepts into formatted widescreen PowerPoint slide decks (`[topic]_presentation.pptx`).
9. **Cumulative Memory Ledger:** Updates a state ledger across academic weeks, ensuring subsequent modules build upon concepts introduced in earlier weeks without redundant backtracking.
10. **Packaging & Lineage Reconciliation:** Packages student dependencies (`requirements.txt`), master curriculum syllabi (`curriculum.json`, `curriculum_grade_[grade].md`), and reconciles bidirectional artifact lineage into `provenance.json`.

### Smart Curriculum Designer Web Portal

The framework includes a modern web portal providing visual workflows for educators and students:

- **Config Studio (`/config`):** Visual curriculum designer with 5-step segmented navigation (`Course & Data`, `Vision Tools`, `Syllabus`, `Weekly Labs`, `Lab Settings`), pre-configured domain presets (Skin Cancer, Plant Diseases, Food-10k), dynamic cluster dataset scanning via Tapis Files API, and a live YAML preview with export capabilities.
- **HPC Job Submission (`/submit`):** 1-click job submission to SDSC Expanse using the Tapis v3 Jobs API. Automatically synchronizes cluster scratch roots, config file locations, Slurm GPU allocation (`--gpus=1`), and Slurm project accounts (`-A uot260`).
- **Live Pipeline Monitor (`/monitor`):** Real-time stage stepper telemetry tracking active pipeline progression (`dataset_ingestion` → `classification` → `segmentation` → `curriculum_synthesis` → `exercise_generation` → `packaging`), cluster heartbeat monitoring, stdout log inspection, and 1-click artifact downloaders.
- **Token & Identity Management (`/token`):** Inspects CILogon / ICICLE Tapis JWTs, provides 1-click 30-day refresh token generation, and handles +4-hour access token renewals.

### Supercomputing Infrastructure (SDSC Expanse & Tapis v3)

- **Cluster Computing:** Scalable compute executed on San Diego Supercomputer Center's (SDSC) Expanse supercomputer utilizing NVIDIA V100/A100 GPU nodes.
- **Fast I/O Scratch Storage:** Jobs execute within dedicated Lustre scratch storage (`/expanse/lustre/scratch/harvest/temp_project/`) for rapid dataset throughput.
- **Tapis v3 Distributed Framework:** Secure job submission, file transfers, and system management using standard Tapis v3 APIs (`/v3/jobs`, `/v3/files`, `/v3/systems`, `/v3/tokens`).
