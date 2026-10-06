# Smart Curriculum Designer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React: 19](https://img.shields.io/badge/React-19-61dafb.svg)](https://react.dev/)
[![TypeScript: 5+](https://img.shields.io/badge/TypeScript-5%2B-3178c6.svg)](https://www.typescriptlang.org/)
[![HPC: Tapis v3](<https://img.shields.io/badge/HPC-Tapis%20v3-orange.svg>)](https://tapis-project.org/)

An AI-driven educational framework that integrates automated curriculum generation with an end-to-end computer vision pipeline, enabling experiential AI literacy learning for K-12 and undergraduate education through real-world datasets.

**Live Web Portal:** [smartcurriculumdesigner.pods.icicleai.tapis.io](https://smartcurriculumdesigner.pods.icicleai.tapis.io)
**Tags:** `AI4CI`, `CI4AI`, `Foundation-AI`, `Visual-Analytics`, `Tapis-v3`, `SDSC-Expanse`

---

## Table of Contents

- [Project Philosophy: The Pipeline is the Curriculum](#project-philosophy-the-pipeline-is-the-curriculum)
- [Key Capabilities](#key-capabilities)
- [System Architecture](#system-architecture)
  - [High-Performance Foundation Vision Pipeline](#high-performance-foundation-vision-pipeline)
  - [Autonomous Multi-Agent Curriculum Engine](#autonomous-multi-agent-curriculum-engine)
  - [Distributed HPC Infrastructure (SDSC Expanse &amp; Tapis v3)](#distributed-hpc-infrastructure-sdsc-expanse--tapis-v3)
- [Smart Curriculum Designer Web Portal](#smart-curriculum-designer-web-portal)
- [Synthesized Educational Artifacts](#synthesized-educational-artifacts)
- [Repository Architecture](#repository-architecture)
- [Documentation &amp; References](#documentation--references)
- [Acknowledgements &amp; Citation](#acknowledgements--citation)
- [Issue Reporting](#issue-reporting)

---

## Project Philosophy: The Pipeline is the Curriculum

Traditional AI education frequently treats machine learning as a simplified black box using synthetic or toy datasets that obscure real-world data science challenges. DigitalAgEdu adheres to the principle that **the pipeline itself is the curriculum**.

Rather than working on generic toy examples, learners execute an authentic foundation model pipeline on domain datasets (e.g., agriculture, dermatology, food sciences). The metrics, class imbalances, confusion matrices, and segmentation masks generated during execution are dynamically injected into scaffolded Python exercises. Students dissect, recreate, optimize, and explain the exact stages they just observed.

```
                  Image Dataset (Any Domain / Kaggle / Tapis)
                                      │
                                      ▼
      [1] Dataset Ingestion         (Class discovery, validation, sample audits)
                                      │
                                      ▼
      [2] DINOv2 Classification     (Transfer learning & robust visual embeddings)
                                      │
                                      ▼
      [3] SAM Segmentation          (Promptable mask extraction & region isolation)
                                      │
                                      ▼
      [4] Visual Explainability     (Grad-CAM heatmaps & Multimodal VLM grounding)
                                      │
                                      ▼
      [5] Multi-Agent Synthesis     (Multi-week syllabus, slide decks, coding exercises)
                                      │
                                      ▼
      [6] Verification Sandbox      (Self-healing unit test generation & test execution)
```

---

## Key Capabilities

- **End-to-End Foundation Model Pipeline:** Integrates Meta's **DINOv2** (Vision Transformer backbone), **Segment Anything (SAM)**, and **Grad-CAM** visual explainability into a coherent workflow.
- **Autonomous Multi-Agent LLM Curriculum Synthesizer:** Multi-agent engine generating overview documents, widescreen PowerPoint presentations (`.pptx`), scaffolded exercises (`.py`), reference solutions, and unit tests (`_test.py`).
- **Interactive Web Portal:** Modern React 19 + TypeScript + Vite web application built with an Obsidian & Zinc frosted glass design system.
- **HPC Supercomputing Integration:** Direct 1-click job submission and Slurm monitoring on **SDSC Expanse** via **Tapis v3 API** (`digital-age-edu-test` / `expanse-tapis-static`).
- **Dynamic Cluster Data Discovery:** Real-time scanning of datasets and user configuration files stored on Tapis systems without hardcoded paths.
- **Zero-Friction Token Lifecycle:** Built-in JWT inspector, 1-click 30-day refresh token generator, and +4-hour token renewals.

---

## System Architecture

The framework decouples compute-intensive machine learning workloads from educational synthesis and web presentation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Web Portal (React 19 + Vite)                    │
│   Config Studio   │   HPC Job Submit   │   Live Monitor   │  Token Hub │
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ HTTPS / Tapis v3 REST
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Tapis v3 Distributed Framework                    │
│   /v3/tokens      │   /v3/files        │   /v3/jobs       │ /v3/systems│
└────────────────────────────────────┬───────────────────────────────────┘
                                     │ Slurm Workload Manager
                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       SDSC Expanse HPC Cluster                         │
│  Lustre Scratch Mount (/expanse/lustre/scratch/harvest/temp_project/)  │
│  App: digital-age-edu-test  |  GPU Queue  |  Slurm: -A uot260          │
│                                                                        │
│  [Pipeline Stages]                                                     │
│   ├── DINOv2 Vision Backbone (Feature extraction & classification)     │
│   ├── SAM Segment Anything (Zero-shot mask extraction)                 │
│   ├── Grad-CAM Heatmaps (Visual evidence & saliency)                   │
│   ├── Agent 0: Overview & Context Synthesizer                          │
│   ├── Agent 1: Scaffolded Exercises & Solutions Generator              │
│   ├── Agent 2: Sandboxed Unit Test Generator & Verifier                │
│   └── Artifact Packager (curriculum.json, .md, .pptx, results.csv)     │
└────────────────────────────────────────────────────────────────────────┘
```

### High-Performance Foundation Vision Pipeline

- **DINOv2 (Vision Transformer Backbone):** Employs self-supervised ViT representations to extract domain-invariant image features. Enables high-precision transfer learning without massive labeled datasets.
- **Segment Anything Model (SAM):** Provides zero-shot promptable segmentation to isolate key regions of interest (e.g., skin lesions, leaf fungal patches, food items).
- **Grad-CAM & Multimodal Grounding:** Produces class activation heatmaps so students understand which visual features influenced classification decisions.

### Autonomous Multi-Agent Curriculum Engine

The engine in `digitalagedu/core/llm/` runs a 3-agent cooperative synthesis pipeline:

- **Agent 0 (Overview & Context Synthesizer):** Analyzes dataset distribution and model performance metrics to author topic background, learning objectives, and domain context (`[topic]_overview.md`).
- **Agent 1 (Exercise & Solution Scaffolder):** Generates structured student exercises with comprehensive docstrings, hints, and `# TODO` milestones (`[topic]_exercise.py`), alongside fully implemented reference implementations (`[topic]_solution.py`).
- **Agent 2 (Verifier & Sandbox Tester):** Writes property-based test suites (`[topic]_test.py`) and executes them in an isolated sandbox, automatically applying self-healing repair loops to ensure student starter code passes baseline structural criteria.
- **Presentation Engine:** Compiles lesson concepts into formatted widescreen PowerPoint lecture slide decks (`[topic]_presentation.pptx`).

### Distributed HPC Infrastructure (SDSC Expanse & Tapis v3)

- **Cluster Computing:** Workloads run on San Diego Supercomputer Center's (SDSC) **Expanse** supercomputer utilizing NVIDIA V100/A100 GPUs.
- **Shared Scratch & Fast I/O:** Execution systems mount High-Performance Lustre Scratch (`/expanse/lustre/scratch/harvest/temp_project/`) for rapid dataset throughput.
- **Slurm Scheduling:** Managed automatically via Tapis v3 job abstractions, supporting allocation routing (`-A uot260`) and logical GPU partitions.

---

## Smart Curriculum Designer Web Portal

The web portal (`frontend/`) delivers a unified visual interface for designing, deploying, and tracking educational curricula:

| Module / Route                               | Functionality                                                                                                                                                                                                                                     |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Config Studio (`/config`)**        | Visual YAML builder with 5-step capsule navigation (`Course & Data`, `Vision Tools`, `Syllabus`, `Weekly Labs`, `Lab Settings`), dynamic Tapis dataset scanner, and sticky live YAML preview.                                           |
| **Submit Job (`/submit`)**           | 1-click HPC job submission to SDSC Expanse via Tapis v3 Jobs API. Auto-resolves cluster scratch roots, config paths, Slurm queue parameters (`--gpus=1`, `-A uot260`), and live JSON payload inspector.                                       |
| **Pipeline Monitor (`/monitor`)**    | Real-time stage stepper telemetry (`dataset_ingestion` → `classification` → `segmentation` → `curriculum_synthesis` → `exercise_generation` → `packaging`), stdout logs modal, elapsed timers, and 1-click artifact downloaders. |
| **Token Manager (`/token`)**         | Full JWT inspector, claims decoder, 30-day refresh token minter, and TTL configurator.                                                                                                                                                            |
| **Model Playground (`/playground`)** | Interactive visual sandbox for zero-shot inference and mask evaluation.                                                                                                                                                                           |

---

## Synthesized Educational Artifacts

Each successful pipeline execution produces a comprehensive curriculum package ready for classroom or lab instruction:

| Artifact File                   | Format     | Description                                                                                           |
| ------------------------------- | ---------- | ----------------------------------------------------------------------------------------------------- |
| `curriculum.json`             | JSON       | Master machine-readable curriculum syllabus with weekly outlines and performance telemetry.           |
| `curriculum_grade_[grade].md` | Markdown   | Formatted student- and instructor-facing syllabus, learning outcomes, and module rubrics.             |
| `[topic]_presentation.pptx`   | PowerPoint | Widescreen slide deck featuring theoretical foundations, pipeline flowcharts, and evaluation metrics. |
| `[topic]_exercise.py`         | Python     | Scaffolded student coding assignment with step-by-step guidance and`# TODO` blocks.                 |
| `[topic]_solution.py`         | Python     | Complete, verified instructor solution and reference implementation.                                  |
| `[topic]_test.py`             | Python     | Property-based unit test suite for student self-evaluation and automated grading.                     |
| `results.csv`                 | CSV        | Comprehensive test set metrics, class-level precision/recall, and inference durations.                |
| `eval_confusion_matrix.png`   | PNG        | Visual classification confusion matrix heatmap for student diagnostic discussions.                    |

---

## Repository Architecture

```
curriculum_generator/
├── digitalagedu/                     # Core Python pipeline & CLI
│   ├── cli.py                        # Typer CLI entrypoints
│   ├── core/
│   │   ├── config.py                 # Pydantic configuration schemas
│   │   ├── scanner.py                # Dataset scanner & distribution analyzer
│   │   ├── executor.py               # Slurm/Tapis pipeline runner
│   │   └── llm/                      # Multi-agent curriculum synthesis
│   │       ├── agent_overview.py     # Agent 0: Overview & context
│   │       ├── agent_exercises.py    # Agent 1: Code exercises & solutions
│   │       └── agent_verifier.py     # Agent 2: Sandboxed unit tests
│   └── models/                       # DINOv2, SAM, and Grad-CAM stages
├── frontend/                         # Modern React 19 + TypeScript + Vite web app
│   ├── src/
│   │   ├── components/
│   │   │   ├── config/               # Config Studio form sections & CapsuleNav
│   │   │   ├── submit/               # HPC job submission cards & payload preview
│   │   │   ├── monitor/              # Pipeline steppers, telemetry & downloaders
│   │   │   ├── token/                # JWT inspector & token minting forms
│   │   │   ├── login/                # Authentication forms
│   │   │   └── navbar/               # User profile dropdown & token quick-renew
│   │   ├── pages/                    # ConfigPage, SubmitJobPage, MonitorPage, etc.
│   │   ├── presets/                  # Domain presets (Skin Cancer, Plant, Food)
│   │   └── utils/
│   │       ├── tapisJobs.ts          # Tapis v3 Jobs, Systems, and Files APIs
│   │       ├── jwt.ts                # Client-side JWT parsing & validation
│   │       └── yamlGenerator.ts      # Pure YAML curriculum generator
│   └── package.json
├── scripts/                          # Deployment & utility scripts
│   ├── sync_frontend_to_pod.py       # Live deployment script for Tapis Pods
│   ├── frontend_pod.py               # Pod creation & resource configuration
│   └── setup_nginx_proxy.py          # Reverse proxy setup for Tapis APIs
├── curriculum_resources/             # Reference materials and model assets
├── documentation/                    # In-depth tutorials and YAML guides
├── app.json                          # Tapis v3 Application Definition
├── run_pipeline.py                   # Standalone local/cluster execution script
└── pyproject.toml                    # Poetry Python dependencies
```

---

## Documentation & References

- **[HOW_TO_USE.md](./documentation/HOW_TO_USE.md):** Step-by-step tutorial for selecting presets and running end-to-end curriculum generation.
- **[YAML_CONFIG_GUIDE.md](./documentation/YAML_CONFIG_GUIDE.md):** Complete specification and field reference for curriculum configuration files.
- **[Tapis v3 Project](https://tapis-project.org):** Documentation for the distributed compute framework powering cluster execution.
- **[DINOv2 Research](https://github.com/facebookresearch/dinov2):** Meta AI's self-supervised vision transformer foundation model.
- **[Segment Anything (SAM)](https://github.com/facebookresearch/segment-anything):** Meta AI's foundation model for promptable image segmentation.

---

## Acknowledgements & Citation

Developed at **The Ohio State University** ([Systems and AI Lab](https://u.osu.edu/sai/), advised by Dr. Hari Subramoni), subsequently submitted to and implemented as part of the **AI Presidential Challenge**.

Special thanks to:

- **Dr. Scott Shearer** and **Dr. Lisa Abrams** (Domain expertise and educational framework design)
- **Columbus School for Girls** (Pilot deployment and classroom evaluation)
- **San Diego Supercomputer Center (SDSC)** (Expanse compute resources via allocation `uot260`)
- **ICICLE AI Institute** (NSF Award #2112606)

If you use this framework in your research or educational curriculum, please cite:

```bibtex
@software{smart_curriculum_designer,
  author = {Jason Seh and Hari Subramoni},
  title = {Smart Curriculum Designer: Automated Foundation AI Curriculum Generation for Experiential Learning},
  year = {2026},
  url = {https://github.com/OSU-SAI-Lab/curriculum_generator}
}
```

---

## Issue Reporting

Please open an issue at [github.com/OSU-SAI-Lab/curriculum_generator/issues](https://github.com/OSU-SAI-Lab/curriculum_generator/issues) with a description of the problem, steps to reproduce, and any relevant logs from pipeline runs or cluster jobs.
