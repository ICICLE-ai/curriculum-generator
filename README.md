# DigitalAgEdu

An AI-driven educational framework that integrates automated curriculum generation with an end-to-end agricultural computer vision pipeline, enabling experiential AI literacy learning for K-12 students through real-world datasets.

**Tags:** `Digital-Agriculture` `AI4CI` `Foundation-AI` `Visual-Analytics`

---

## License

MIT License

---

## Acknowledgements

```markdown
This project was developed as a Master's thesis at The Ohio State University (Systems and AI Lab, advised by Dr. Hari Subramoni), subsequently submitted to and implemented as part of the AI Presidential Challenge, and integrated with the NSF-funded ICICLE AI Institute.

National Science Foundation (NSF) funded AI institute for Intelligent Cyberinfrastructure with Computational Learning in the Environment (ICICLE) (OAC 2112606)

Additional thanks to Dr. Shearer Scott and Dr. Lisa Abrams for domain expertise, dataset access, and educator feedback, and to the Columbus School for Girls for pilot deployment support.
```

---

## Tutorials

### Getting Started: Generate a Curriculum and Run the AI Pipeline

This tutorial walks you through the complete DigitalAgEdu workflow from installation to running the AI pipeline on an agricultural dataset.
 - /fs/ess/PAS2699/mhole/curriculum_generator/Code/getting_started/getting_started.mov

**Prerequisites**

- Python 3.8 or higher installed on your machine
- A terminal or command prompt
- An image dataset — either one of the provided sample datasets (see below) or your own images organized in the required folder structure
- *(Recommended for datasets over 500 images)* A GPU-enabled machine or access to OSC Pitzer cluster

---

**Supported Use Cases**

- **Sample datasets used in this project:**
  - [Soybean Leaf Disease Dataset](/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Soybeans/Soybeans) — available on OSC
  - [Corn Leaf Disease Dataset](/fs/ess/PAS2699/AI_Presidency_Dataset_CSG/Corn/Corn) — available on OSC
  - [Corn Residue Cover Analysis](/fs/ess/PAS2699/crdean95) — available on OSC (GP Tillage Test 1-4)
  - [Soil Aggregate Size Analysis](/fs/ess/PAS2699/crdean95) — available on OSC (GP Tillage Test 1-4)

---

**Getting Sample Data**

If you do not have your own dataset, you can download one of the publicly available datasets used in this project. The steps below use the Soybean dataset from Kaggle as an example.

1. Create a free account at [kaggle.com](https://www.kaggle.com) if you do not already have one.
2. Go to the [PlantVillage dataset page](https://www.kaggle.com/datasets/emmarex/plantdisease) and click **Download**.
3. Unzip the downloaded file. You will get a folder of images organized by class label, for example:
   ```
   PlantVillage/
   ├── Soybean___healthy/
   ├── Soybean___bacterial_blight/
   ├── Soybean___caterpillar/
   └── Soybean___diabrotica_specimen/
   ```
4. Note the full path to this folder on your computer — you will need it in Step 2 below.

---

**Using Your Own Data**

You can use DigitalAgEdu with your own agricultural image dataset. Your images must be organized in the following folder structure before running the pipeline:

```
your_dataset/
├── class_name_1/
│   ├── image001.jpg
│   ├── image002.jpg
│   └── ...
├── class_name_2/
│   ├── image001.jpg
│   └── ...
└── class_name_N/
    └── ...
```

- Each subfolder name becomes a class label. Use clear, descriptive names (e.g., `healthy`, `bacterial_blight`).
- Supported image formats: `.jpg`, `.jpeg`, `.png`
- Images do not need to be the same size — the pipeline handles resizing automatically.
- **Minimum recommended dataset size:** 50 images per class for curriculum generation. For reliable AI pipeline results, aim for at least 100–200 images per class.

> **GPU guidance — when do you need one?**
>
> | Dataset size | Hardware recommendation |
> |---|---|
> | Under 200 images total | CPU is sufficient; pipeline completes in a few minutes |
> | 200–500 images | CPU works but may take 20–60 minutes; GPU is recommended |
> | 500–2,000 images | GPU strongly recommended; CPU may take several hours |
> | Over 2,000 images | GPU required; consider using OSC Pitzer cluster (see How-To Guides) |
>
> The curriculum generation step (Step 3 below) does not require a GPU regardless of dataset size — it only reads metadata, not the images themselves.

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
| `dataset_path` | Full path to your dataset folder on your computer (e.g., `/Users/yourname/Downloads/PlantVillage`) |
| `grade_level` | Target grade level (e.g., `"6-8"` or `"9-12"`) |
| `topics` | Topics you want the curriculum to cover |
| `num_classes` | Number of class subfolders in your dataset |

Save the file with a descriptive name, such as `corn_config.yaml`.

> **Finding your dataset path:**
> - On **Mac/Linux:** right-click the dataset folder → Get Info → copy the path shown under "Where"
> - On **Windows:** hold Shift and right-click the folder → "Copy as path"

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

Replace the placeholder with the actual path to your dataset folder — the same path you used in `sample_config.yaml` — then run:

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

### How to Run on the OSC Pitzer Cluster (Large Datasets)

**Problem:** Your dataset is too large to process on a personal computer, or processing is taking too long on CPU.

1. Log in to OSC OnDemand at [ondemand.osc.edu](https://ondemand.osc.edu).
2. Upload your dataset to your OSC home directory using the Files menu.
3. Open a terminal in the project directory and set the dataset path in `run_pipeline.py` to your OSC path, for example:
   ```python
   DATASET_PATH = "/users/PAS0000/yourname/your_dataset"
   ```
4. Submit the pipeline as a batch job using the provided job script:
   ```bash
   sbatch run_pipeline.sh
   ```
5. Monitor the job status with:
   ```bash
   squeue -u yourname
   ```

---

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
| Pipeline is very slow | Your dataset likely exceeds 500 images — a GPU is recommended. See the OSC Pitzer guide above |
| Images not loading | Check that all images are in `.jpg`, `.jpeg`, or `.png` format and that each class has its own subfolder |
| Generated curriculum looks too generic | Ensure `num_classes`, `grade_level`, and `topics` in your config file are as specific as possible |
| `dataset_path` not found error | Double-check the path in your `.yaml` file. On Windows, use forward slashes (`/`) or escape backslashes (`\\`) |

---

## Explanation

### System Overview

DigitalAgEdu has two independent but connected components that share a common dataset:

1. **Curriculum Generation Engine** (`digitalagedu/core/`) — reads dataset metadata from a YAML config and produces a structured, ABET-aligned weekly learning plan. The engine derives instructional structure from real dataset properties (number of classes, class imbalance ratios, estimated visual difficulty) rather than from static templates. This step does not process images — it only reads the config file, so no GPU is needed.

2. **AI Pipeline** (`run_pipeline.py`) — runs the full computer vision pipeline on the same dataset, producing outputs that students directly analyze as part of the curriculum. This step processes every image in the dataset and is compute-intensive for larger collections.

### Dataset Requirements and Expectations

The pipeline is designed to work with real agricultural field or lab images. The following guidelines apply whether you are using a sample dataset or your own:

- **Image quality:** standard smartphone or camera photos work well. Images do not need to be taken with specialized equipment.
- **Class balance:** results are most reliable when classes have a similar number of images. If one class has significantly more images than others, the classifier may be biased toward it.
- **Image variety:** include images taken at different lighting conditions, angles, and growth stages if possible. A diverse dataset leads to more robust classification.
- **Dataset size and GPU needs:** the pipeline can run on a regular laptop CPU for small datasets (under ~200 images), but GPU support becomes important as dataset size grows — see the GPU guidance table in the tutorial section above.

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