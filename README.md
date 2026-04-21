# DigitalAgEdu

An AI-driven educational framework that integrates automated curriculum generation with an end-to-end agricultural computer vision pipeline, enabling experiential AI literacy learning for K-12 students through real-world datasets.

**Tags:** `Digital-Agriculture` `AI4CI` `Foundation-AI` `Visual-Analytics`

---

## References

- [DINOv2: Learning Robust Visual Features without Supervision](https://arxiv.org/abs/2304.07193)
- [Segment Anything Model (SAM)](https://arxiv.org/abs/2304.01301)
- [ICICLE AI Institute](https://aiira.iastate.edu/resources/icicle/)
- [Ohio Supercomputer Center (OSC) — Pitzer Cluster](http://osc.edu/ark:/19495/hpc4w3dh5)
- [Bloom's Taxonomy of Educational Objectives](https://www.bloomstaxonomy.net/)
- [ABET Criteria for Accrediting Computing Programs](https://www.abet.org/accreditation/accreditation-criteria/criteria-for-accrediting-computing-programs-2023-2024/)
- [AI Literacy Framework — Ng et al. (2021)](https://doi.org/10.1016/j.caeai.2021.100041)
- **Key terms:**
  - *Curriculum Generation Engine (CGE)* — the metadata-driven module that produces structured weekly learning plans from dataset properties
  - *SAM* — Segment Anything Model; used for zero-shot leaf segmentation
  - *DINOv2* — self-supervised Vision Transformer backbone used for image classification
  - *HITL* — Human-in-the-Loop; manual expert review and adjustment of generated outputs before classroom deployment

---

## Acknowledgements

This project was developed as part of the AI Presidential Challenge in collaboration with ICICLE and the Columbus School for Girls.

National Science Foundation (NSF) funded AI institute for Intelligent Cyberinfrastructure with Computational Learning in the Environment (ICICLE) (OAC 2112606)

Additional thanks to Dr. Hari Subramoni (The Ohio State University Systems and AI Lab), Dr. Shearer Scott, and Dr. Lisa Abrams for domain expertise, dataset access, and educator feedback.

---

## Tutorials

### Getting Started: Generate a Curriculum and Run the AI Pipeline

This tutorial walks you through the complete DigitalAgEdu workflow from installation to running the AI pipeline on an agricultural dataset. No prior machine learning experience is required.

**Prerequisites**

- Python 3.8 or higher installed on your machine
- Access to an agricultural image dataset in one of the four supported formats (see Supported Use Cases below)
- A terminal or command prompt
- *(Recommended)* A GPU-enabled machine or access to OSC Pitzer cluster for running the AI pipeline

**Supported Use Cases**

| Use Case | Description |
|---|---|
| Soybean Disease Detection | Leaf-level classification across 4 disease classes |
| Corn Disease Classification | Leaf-level classification across 13 classes |
| Corn Residue Cover Analysis | Field-level residue coverage estimation |
| Soil Aggregate Size Analysis | Soil sample classification and quantification |

---

**Step 1 — Install Dependencies**

Open a terminal in the project root directory and run:

```bash
pip install -r requirements.txt
```

If you are on a shared computing cluster (e.g., OSC Pitzer), use:

```bash
pip install -r requirements.txt --user
```

---

**Step 2 — Prepare Your Configuration File**

Open `sample_config.yaml` in any text editor. Edit the following fields to match your dataset:

```yaml
dataset_name: "Soybean Disease"
dataset_path: "/path/to/your/dataset"
grade_level: "9-12"
topics:
  - "Image Classification"
  - "Disease Detection"
num_classes: 4
```

| Field | What to change |
|---|---|
| `dataset_name` | Name of your dataset (e.g., `"Corn Disease"`) |
| `dataset_path` | Full path to your dataset folder |
| `grade_level` | Target grade level (e.g., `"6-8"` or `"9-12"`) |
| `topics` | Topics you want the curriculum to cover |
| `num_classes` | Number of classes in your dataset |

Save the file with a descriptive name, such as `corn_config.yaml`.

---

**Step 3 — Generate the Curriculum**

Run the following command:

```bash
python -m digitalagedu.cli generate sample_config.yaml --output soybean_output.json
```

| Part of the command | What it is | What to change it to |
|---|---|---|
| `sample_config.yaml` | Your input configuration file | The name of the config file you saved in Step 2 (e.g., `corn_config.yaml`) |
| `soybean_output.json` | The output curriculum file | Any descriptive name ending in `.json` (e.g., `corn_curriculum.json`) |

**Example for a corn dataset:**
```bash
python -m digitalagedu.cli generate corn_config.yaml --output corn_curriculum.json
```

The output is a JSON file containing a 16-week structured learning plan with week-by-week objectives, pacing recommendations, and predicted learning outcomes aligned to ABET Student Outcomes and Bloom's Taxonomy.

---

**Step 4 — Review and Adjust the Output (Human-in-the-Loop)**

Open the generated `.json` file in any text editor. Review it before using it with students. Ask yourself:

- Is the week-by-week pacing realistic for your classroom schedule?
- Do the predicted learning outcomes match your instructional goals?
- Are any topics missing, redundant, or out of order for your cohort?

The generated curriculum is a starting point. Your judgment as an educator is essential to making it effective.

---

**Step 5 — Set the Dataset Path and Run the AI Pipeline**

Open `run_pipeline.py` in a text editor and update the dataset path near the top of the file:

```python
DATASET_PATH = "/path/to/your/dataset"
```

Replace the placeholder with the actual path to your dataset, then run:

```bash
python run_pipeline.py
```

The pipeline will automatically run image classification (DINOv2), leaf segmentation (SAM), and damage estimation (HSV analysis) and save results to the configured output directory.

---

**End Result**

After completing this tutorial you will have:
- A generated `.json` file (e.g., `soybean_output.json`) containing your 16-week curriculum plan
- Classification predictions, segmentation masks, and damage estimates for your dataset saved to the output folder

---

## How-To Guides

### How to Swap in a Different Model

**Problem:** You want to replace DINOv2 or SAM with a different open-source model.

1. Open `curriculum_resources/models.json`. This file lists all currently integrated models with their names, sources, and configuration keys.
2. Find the entry for the model you want to replace and update it with the new model's details.
3. Update the corresponding model loading call in `run_pipeline.py` to point to the new model.
4. Re-run the pipeline to verify the new model loads and runs correctly.

---

### How to Use the Prerequisites Materials

**Problem:** Your students have little or no background in AI or Python before starting the curriculum.

1. Navigate to `curriculum_resources/prerequisites/`.
2. Direct students to `ai_basics/` first — this self-contained module takes approximately 40–60 minutes and requires no prior experience.
3. Then direct students to `python_basics/` for links to official Python documentation and beginner exercises. Students should be comfortable with Python before Week 3 of the curriculum.

---

### How to Use the Weekly Curriculum Folders

**Problem:** You want to know what materials are available for each week and how to distribute them to students.

Each `curriculum_resources/week_XX/` folder contains:

| File | Purpose |
|---|---|
| `README.md` | Week overview, learning goals, and curated resources |
| `starter_code.py` | Student-facing code with TODO markers |
| `solution_code.py` | Complete reference implementation for instructors |

Share only `starter_code.py` with students. Use `solution_code.py` as a grading and discussion reference.

---

### Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` when running the CLI | Make sure you are running the command from the project root directory (the folder containing `digitalagedu/` and `requirements.txt`) |
| `CUDA out of memory` error | Lower the `BATCH_SIZE` variable in `run_pipeline.py` (e.g., from `16` to `4`) |
| Pipeline is very slow | The pipeline is optimized for GPU. Running on CPU will be significantly slower — use a GPU-enabled machine or cluster if available |
| Generated curriculum looks too generic | Ensure `num_classes`, `grade_level`, and `topics` in your config file are as specific as possible |

---

## Explanation

### System Overview

DigitalAgEdu has two independent but connected components that share a common dataset:

1. **Curriculum Generation Engine** (`digitalagedu/core/`) — reads dataset metadata from a YAML config and produces a structured, ABET-aligned weekly learning plan. The engine derives instructional structure from real dataset properties (number of classes, class imbalance ratios, estimated visual difficulty) rather than from static templates.

2. **AI Pipeline** (`run_pipeline.py`) — runs the full computer vision pipeline on the same dataset, producing outputs that students directly analyze as part of the curriculum.

### Why This Design

Traditional AI education tools either present AI as a black box or use simplified toy datasets that do not reflect how real systems behave. DigitalAgEdu is designed around the principle that the pipeline itself — including its failures, limitations, and performance trade-offs — is the curriculum. Students do not just learn *about* AI; they interact with a production-grade system running on real agricultural data.

### AI Pipeline Stages

```
Image Dataset
     │
     ▼
[1] Image Acquisition        ← Recursive loading from dataset path
     │
     ▼
[2] DINOv2 Classification    ← Transfer learning + fine-tuning on disease classes
     │
     ▼
[3] SAM Segmentation         ← Zero-shot leaf region isolation
     │
     ▼
[4] HSV Damage Estimation    ← Quantitative percentage damage per leaf
     │
     ▼
Output Artifacts             ← Predictions, masks, damage reports
```

### Curriculum Generation

The Curriculum Generation Engine (`digitalagedu/core/`) takes a YAML config describing a dataset and produces a 16-week plan. Key design decisions:

- **Metadata-driven pacing:** the number of weeks allocated to each topic is computed from dataset complexity (class count, imbalance ratio, visual similarity scores), not assigned manually
- **ABET alignment:** every generated curriculum includes predicted learning outcomes mapped to ABET Student Outcomes and Bloom's Taxonomy cognitive levels
- **Human-in-the-Loop:** the engine produces a starting point; educator review and adjustment before deployment is a required step, not an optional one

### Project Structure

```
DigitalAgEdu/
├── digitalagedu/
│   └── core/                   # Curriculum generation engine (all source files)
├── curriculum_resources/
│   ├── models.json             # Open-source model registry (swappable)
│   ├── prerequisites/
│   │   ├── ai_basics/          # ~40-60 min intro to AI concepts
│   │   └── python_basics/      # Official Python documentation links
│   └── week_01/ ... week_16/   # Per-week folders (README, starter code, solution code)
├── run_pipeline.py             # AI pipeline entry point
├── sample_config.yaml          # Example dataset configuration
├── requirements.txt            # Python dependencies
└── README.md
```
