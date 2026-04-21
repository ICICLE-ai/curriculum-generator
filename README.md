# DigitalAgEdu

**An AI-Driven Educational Framework for Agricultural Computer Vision**

DigitalAgEdu is a modular system with two independent but connected components:

1. **Curriculum Generation Engine** — takes dataset metadata and produces a structured, week-by-week learning plan tailored for K-12 students
2. **AI Pipeline** (`run_pipeline.py`) — runs the full computer vision pipeline (classification, segmentation, and damage estimation) on agricultural image datasets

Both components share a common dataset, but can be run independently of each other.

---

## Supported Use Cases

| Use Case | Dataset |
|---|---|
| Soybean Disease Detection | Soybean leaf images (4 disease classes) |
| Corn Disease Classification | Corn leaf images (13 classes) |
| Corn Residue Cover Analysis | Field-level residue coverage images |
| Soil Aggregate Size Analysis | Soil sample images |

---

## Project Structure

```
DigitalAgEdu/
├── digitalagedu/
│   └── core/                   # Curriculum generation engine (all files here)
├── curriculum_resources/
│   ├── models.json             # List of open-source models (swappable)
│   ├── prerequisites/
│   │   ├── ai_basics/          # ~40-60 min intro to AI concepts
│   │   └── python_basics/      # Links to official Python documentation
│   └── week_01/ ... week_16/   # Per-week curriculum folders (see below)
├── run_pipeline.py             # AI pipeline: classification + segmentation + damage estimation
├── sample_config.yaml          # Example dataset configuration file
├── requirements.txt            # All Python dependencies
└── README.md
```

### Per-Week Curriculum Folder Structure

Each `week_XX/` folder inside `curriculum_resources/` contains:

```
week_01/
├── README.md          # Overview and learning resources for that week
├── starter_code.py    # Starter code for students (with TODO markers)
└── solution_code.py   # Complete reference solution
```

---

## Setup

### Step 1 — Install Dependencies

Open a terminal in the project root directory and run:

```bash
pip install -r requirements.txt
```

> If you are on a shared computing cluster (e.g., OSC Pitzer), you may need to use:
> ```bash
> pip install -r requirements.txt --user
> ```

---

## Component 1 — Curriculum Generation

This component reads a configuration file describing your dataset and generates a structured JSON curriculum plan.

### Step 2 — Prepare Your Configuration File

Open `sample_config.yaml` in any text editor. You will see fields like:

```yaml
dataset_name: "Soybean Disease"
dataset_path: "/path/to/your/dataset"
grade_level: "9-12"
topics:
  - "Image Classification"
  - "Disease Detection"
num_classes: 4
```

Edit the following fields to match your dataset:

| Field | What to change |
|---|---|
| `dataset_name` | The name of your dataset (e.g., `"Corn Disease"`) |
| `dataset_path` | The full path to your dataset folder on your computer |
| `grade_level` | Target grade level (e.g., `"6-8"` or `"9-12"`) |
| `topics` | List of topics you want the curriculum to cover |
| `num_classes` | Number of disease/category classes in your dataset |

Save the file with a descriptive name, for example `corn_config.yaml` or `soybean_config.yaml`.

### Step 3 — Generate the Curriculum

Run the following command, replacing the file names as described below:

```bash
python -m digitalagedu.cli generate sample_config.yaml --output soybean_output.json
```

**What to change in this command:**

| Part | What it is | What to change it to |
|---|---|---|
| `sample_config.yaml` | Your input configuration file | The name of the config file you saved in Step 2 (e.g., `corn_config.yaml`) |
| `soybean_output.json` | The output curriculum file | Any name you want, ending in `.json` (e.g., `corn_curriculum.json`) |

**Example for a corn dataset:**
```bash
python -m digitalagedu.cli generate corn_config.yaml --output corn_curriculum.json
```

### Step 4 — Review the Output (Human-in-the-Loop)

Open the generated `.json` file (e.g., `soybean_output.json`) in any text editor or JSON viewer.

The output will contain a 16-week structured learning plan including:
- Week-by-week learning objectives
- Recommended activities and pacing
- Predicted learning outcomes mapped to ABET Student Outcomes and Bloom's Taxonomy levels

**You should review and adjust this output before using it with students.** Things to check:

- Are the pacing and week allocations realistic for your classroom schedule?
- Do the predicted learning outcomes match what you actually want students to achieve?
- Are there any topics that should be added, removed, or reordered for your specific cohort?

The generated curriculum is a starting point — your expertise as an educator is essential to make it work well for your students.

---

## Component 2 — AI Pipeline

This component runs the full computer vision pipeline on your dataset: image classification, leaf segmentation, and percentage damage estimation.

### Step 5 — Set the Dataset Path in `run_pipeline.py`

Open `run_pipeline.py` in a text editor. Find the line that sets the dataset path (near the top of the file):

```python
DATASET_PATH = "/path/to/your/dataset"
```

Replace `/path/to/your/dataset` with the actual path to your dataset folder on your computer or cluster.

**Example:**
```python
DATASET_PATH = "/users/jsmith/data/soybean_images"
```

Save the file.

### Step 6 — Run the Pipeline

```bash
python run_pipeline.py
```

The pipeline will run through the following stages automatically:

1. **Image Acquisition** — loads images from the dataset path you set
2. **Classification** — uses DINOv2-based transfer learning to classify each image
3. **Segmentation** — uses SAM (Segment Anything Model) to isolate leaf regions
4. **Damage Estimation** — uses HSV-based analysis to estimate percentage of damage per leaf

Pipeline outputs (predictions, segmentation masks, damage estimates) will be saved in the output directory specified inside `run_pipeline.py`.

> **Note:** Running the pipeline on a GPU is strongly recommended. On a CPU, processing will be significantly slower. If you have access to OSC Pitzer cluster nodes, use the provided job scripts.

---

## Curriculum Resources

### `curriculum_resources/models.json`

This file lists the open-source models currently integrated into the pipeline (DINOv2, SAM, etc.). If you want to swap in a different model, edit the relevant entry in this file and update the corresponding call in `run_pipeline.py`.

### `curriculum_resources/prerequisites/`

Before starting the 16-week curriculum, students (and instructors new to AI) should work through the prerequisites:

- **`ai_basics/`** — A self-contained introduction to AI and computer vision concepts, designed to take approximately 40–60 minutes. No prior experience required.
- **`python_basics/`** — Links to official Python documentation and beginner exercises. Students should be comfortable with Python basics before Week 3 of the curriculum.

### `curriculum_resources/week_01/` through `week_16/`

Each week's folder contains a `README.md` with the week's topic, learning goals, and curated resources, a `starter_code.py` file with TODO markers where students fill in code, and a `solution_code.py` with the complete reference implementation. Instructors should share only `starter_code.py` with students and use `solution_code.py` as a grading reference.

---

## Quick Reference — All Commands

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate curriculum from a config file
python -m digitalagedu.cli generate sample_config.yaml --output soybean_output.json

# 3. Run the AI pipeline
python run_pipeline.py
```

---

## Troubleshooting

**`ModuleNotFoundError` when running the CLI**
Make sure you are running the command from the project root directory (the folder that contains `digitalagedu/` and `requirements.txt`).

**`CUDA out of memory` error**
Reduce the batch size in `run_pipeline.py` by finding the `BATCH_SIZE` variable and lowering it (e.g., from `16` to `4`).

**Pipeline is very slow**
The pipeline is optimized for GPU. If running on CPU, expect significantly longer processing times. Consider running on a GPU-enabled machine or cluster.

**Generated curriculum looks too generic**
Make sure your `sample_config.yaml` has accurate values for `num_classes`, `grade_level`, and `topics`. The more specific your config, the more tailored the generated curriculum will be.

