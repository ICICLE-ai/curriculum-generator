# YAML Configuration Guide

Every Smart Curriculum Designer run is described by one YAML configuration file: your subject, your images, the vision tools to run, and the weeks of the course. **You normally never write this file by hand.** The **Curriculum Config** page of the portal builds it for you as you fill in the form, shows a live preview, and saves it with **Export to Tapis**. This guide explains what each setting does, for when you want to understand or fine-tune a configuration.

A complete example is at the [end of this guide](#sample-yaml-config).

____________________________________________________________________________

### Settings

#### Project
- **`domain`:** The field your course is about (e.g. "Agricultural Crop Health"). The AI uses it to ground the course, lessons and examples in your field.
- **`context_statement`:** The real-world problem students work on (e.g. "identifying crop leaf blight and foliar pathogens"). It shapes the course plan and each week's problem statement.
- **`use_case`:** A label for your own reference. It does not change the output.

#### Dataset
- **`root_path`:** The folder holding your images on the cluster. It must contain one subfolder per category, named after the category:
  ```
  food/
       |_pasta/
       |_pizza/
       |_etc./
  ```
  The portal fills this in when you choose a dataset from the cluster, upload one, or transfer one from a URL.

#### Output
- **`directory`:** Where results are written inside the job's folder (e.g. `./outputs/plant_diseases_v1`). The weekly materials go in its `exercises/` subfolder.

#### Pipeline
- **`stages`:** The vision tools run on your images, in this order: Classification (DINOv2) → Segmentation (SAM) → VisualXAI (Grad-CAM heatmaps). Each stage has:
  - **`name`:** `Classification`, `Segmentation` or `VisualXAI`.
  - **`active`:** `true` to run the stage, `false` to skip it. The lessons are built from what the stages produce, so turning a stage off also removes it from the material the lessons can draw on.
  - **`task_type`:** A descriptive label (e.g. `crop_disease_classification`).
  - **`prompt`** (Segmentation only): A short description of what to outline (e.g. "the diseased leaf spot"). A text-prompted detector finds it in each image and SAM outlines it. In images where nothing matches, and when the prompt is left out, SAM outlines the most prominent object. The job log reports how many images the prompt matched.

#### Execution
- **`device`:** `"cuda"` to run on the cluster's GPU (recommended), or `"cpu"` (much slower).
- **`batch_size`:** How many images are processed at once. Lower it (e.g. from 16 to 4) if the job runs out of GPU memory.
- **`image_size`:** The size images are resized to. Keep 518, the size DINOv2 is designed for.
- **`max_samples`:** How many images to use, split evenly across your categories (e.g. 500). Leave it out to use the whole dataset. A smaller number makes the vision pipeline faster.
- **`seed`:** Any whole number. Using the same seed with the same data picks the same images and splits, so a run can be reproduced.
- **`use_llm`:** `true` (the default) generates the weekly lessons, code and slides. `false` runs only the vision pipeline.
- **`llm_models`** *(optional)*: Which AI model does each job. Set in the portal under **AI Lesson Writer Models**; leave it out to use the defaults:

  | Role | Default | What it does |
  | --- | --- | --- |
  | `planner` | `deepseek-v4-flash` | Plans the course and writes each week's problem statement |
  | `coder` | `glm-5` | Writes the tests, the solution and the student starter code, and repairs them |
  | `arbiter` | `deepseek-v4-flash` | Decides whether the tests or the solution is wrong when they keep disagreeing |
  | `slides` | `glm-5` | Builds the lecture slides |
  | `slide_reviewer` | `deepseek-v4-flash` | Checks a screenshot of each slide; must be a model that can read images |

- **Advanced settings** you can leave out: `parallel_weeks` (how many weeks are built at once; by default up to four), `llm_concurrency`, `llm_base_url` (the project's AI service; only change it if you run the pipeline yourself with your own NRP key in `NRP_LLM_API`, in which case set it to `https://ellm.nrp-nautilus.io/v1`), and the `use_qdrant_rag` / `qdrant_*` knowledge-base settings.

#### Curriculum
- **`subject`:** The course title, shown on the generated syllabus.
- **`target_level`** or **`grade`:** The students' level (e.g. "Grade 10" or "Undergraduate"). The portal writes `target_level`; if both are set, `target_level` wins, and with neither the course is planned for Grade 10. The level shapes the course plan, every week's problem statement, code, tests and slides, and the syllabus file name.
- **`modules`:** The weeks of your course. Each module has:
  - **`id`:** A short name with no spaces (e.g. `leaf_image_exploration`). It names the week's folder and files.
  - **`title`:** The week's title.
  - **`week`:** The week number (1–24). Two modules can share a week.
  - **`difficulty`:** `beginner`, `intermediate` or `advanced`.
  - **`context`:** What the week should teach, in a sentence or two. This is the main instruction the AI follows, so be specific.
  - **`learning_outcomes`:** Two or three things students should be able to do by the end of the week.
- **`topics`:** Used only when `modules` is empty: each topic becomes one week.
  - **`name`**, **`description`**, **`project`:** The topic's name, a description, and the project it belongs to.
- **`weeks`:** Used only when the AI plans the course: how many weeks to plan (4–24, default 6). The portal does not set it; add it by hand for a different length.
- **`resources`:** Links for students (e.g. the dataset's source), each with a **`name`** and **`url`**. Recorded in the course's `curriculum.json`.

**How the weeks are decided:**
1. If `modules` lists any weeks, those are used.
2. Otherwise, if `topics` lists any topics, each topic becomes a week.
3. Otherwise, a Syllabus Architect plans the whole course (`weeks` long) from your subject, problem statement and dataset.

____________________________________________________________________________

### Saving Your Configuration to the Cluster

1. On the **Curriculum Config** page, click **Export to Tapis**. The file is saved to your configuration folder on the cluster (`smart_curriculum_designer_configs`).
2. On **Submit Job**, your exported file appears in the list of discovered configurations. Click it to use it.

To keep a copy, use the download button on the YAML preview. If you edit a configuration by hand, upload it to the same `smart_curriculum_designer_configs` folder through the Files page of the [Tapis portal](https://icicleai.tapis.io/#/home) so that it appears on **Submit Job**.

---

### Sample YAML Config

This is the **Crop Leaf Disease Detection** preset from the portal, with the learning outcomes shortened.

```yaml
# ===============
# Project Context
# ===============
project:
  domain: "Agricultural Crop Health"
  context_statement: "identifying crop leaf blight and foliar pathogens in agricultural fields"
  use_case: "plant_diseases"

# ================
# Dataset Settings
# ================
dataset:
  root_path: "/expanse/lustre/scratch/harvest/temp_project/shared/smart_curriculum_designer_datasets/plant_dataset"

# ================
# Output Directory
# ================
output:
  directory: "./outputs/plant_diseases_v1"

# ================
# Pipeline Stages
# ================
pipeline:
  stages:
    - name: "Classification"
      active: true
      task_type: "crop_disease_classification"
    - name: "Segmentation"
      active: true
      task_type: "object_extraction"
      prompt: "the diseased leaf spot or infected foliage"
    - name: "VisualXAI"
      active: true
      task_type: "visual_explainability"

# ============
# Execution
# ============
execution:
  device: "cuda"
  batch_size: 16
  image_size: 518
  max_samples: 500
  seed: 6767
  use_llm: true

# ==================
# Curriculum Config
# ==================
curriculum:
  subject: "Intro to Agricultural AI: Plant Disease Detection"
  target_level: "Undergraduate / Grade 10"

  modules:
    - id: "leaf_image_exploration"
      title: "Agricultural Imaging & Foliar Symptom Exploration"
      week: 1
      difficulty: "beginner"
      context: "Inspect foliar lesion patterns, color channel distributions, and class balance in plant pathology datasets."
      learning_outcomes:
        - "Calculate pathogen class distributions, identifying minority blight classes and class imbalance."
        - "Build exploratory image processing pipelines to compute greenness indices and color channel histograms."
    - id: "morphological_feature_extraction"
      title: "Handcrafted Morphological Descriptors & Baseline Classifiers"
      week: 2
      difficulty: "intermediate"
      context: "Extract texture (GLCM), color moment, and lesion shape features to train classical machine learning baselines."
      learning_outcomes:
        - "Extract gray-level co-occurrence matrix (GLCM) texture features and color moments from leaf lesions."
        - "Train classical baseline models (support vector machines, random forests) on extracted features."
    - id: "dinov2_representation_learning"
      title: "Self-Supervised Feature Embeddings with DINOv2"
      week: 3
      difficulty: "intermediate"
      context: "Extract visual embeddings from a pre-trained DINOv2 model and train PyTorch classification heads on them."
      learning_outcomes:
        - "Extract 768-dimensional visual tokens using a pre-trained DINOv2 backbone."
        - "Visualize how disease classes separate in the embedding space with PCA and t-SNE."
    - id: "sam_zero_shot_segmentation"
      title: "Zero-Shot Foliar Lesion Segmentation with SAM"
      week: 4
      difficulty: "intermediate"
      context: "Use the Segment Anything Model (SAM) to outline infected regions on leaves and measure damaged area."
      learning_outcomes:
        - "Generate segmentation masks with SAM to measure the share of the leaf that is damaged."
        - "Measure mask quality with Intersection-over-Union (IoU)."

  resources:
    - name: "PlantVillage Benchmark Dataset"
      url: "https://github.com/spMohanty/PlantVillage-Dataset"
    - name: "Segment Anything (SAM) Repository"
      url: "https://github.com/facebookresearch/segment-anything"
```
