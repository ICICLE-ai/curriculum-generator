# Sprint Three - Bridging Pipeline & Curriculum Generation

## Overview

For this iteration, the main goal is to bridge the pipeline and the syllabus generation to produce a usable output for the educator to use for AI education. By taking the outputs of the pipeline and the week-by-week suggestions of the syllabus, we can create exercises relating to the week’s goals.

### Existing Resources

A few of the weeks will typically have tasks like "analyze the dataset", "review the confusion matrix", and generally reviewing outputs. Since the pipeline itself already outputs all metrics of the original run including things like accuracy, precision, confusion matrices, etc. they can be used as a guide for the student when writing their own solutions or as a hands-on example of what a successful execution looks like.

### Practice Generation

To bridge the gap between the pipeline and the syllabus, we can create practice tasks and coding exercises tailored for each week. Using the existing pipeline and its outputs as a basis, along with Jinja templates, it is possible to create domain-agnostic exercises.

The generation workflow is structured as follows:

* **Dynamic Scaffolding:** For each week, generate starter templates, solution keys, and unit test suites dynamically using the Jinja template.
* **Positive/Negative Subprocess Verification:** Create unit tests for both the solution keys and starter templates. Using a subprocess, run the tests to verify the generated exercises execute correctly and produce the intended output (solutions must pass, starters must fail/require student input).

---

## Technology Stack & Tooling

To implement this workflow, the following technologies and libraries are leveraged:

### 1. Verification & Sandboxing

* **`subprocess` (Python Standard Library):** Used to launch sandboxed Python processes (`python test_exercise.py`) in isolated environments to verify exit codes and execution outputs.
* **`tempfile` (Python Standard Library):** Creates temporary, isolated workspace directories for compiling, running, and destroying intermediate testing scripts, keeping the main repository clean.
* **`unittest` (Python Standard Library):** The target unit-test framework for writing assertion suites. It provides readable test outputs and structured exit codes (0 for pass, non-zero for failures).

### 2. Code Templating & Parsing

* **`Jinja2`:** Extends the existing template rendering system to dynamically inject database properties, metric statistics, and configuration values into the starter code and test suites.
* **Abstract Syntax Trees (`ast` library) / Delimiter Parser:** Used to parse code blocks in the solution scripts to automatically split student segments (`[STUDENT_STARTER]`) from instructor solutions (`[REFERENCE_SOLUTION]`).

### 3. Student Environment Dependencies

* **`PyTorch` (`torch`, `torchvision`):** Used by students to implement classification layers, neural network heads, and standard tensor preprocessing.
* **`OpenCV` (`opencv-python`):** The primary library for image manipulation, cropping, calculating mask bounding boxes, and drawing overlays.
* **`Transformers` / Model Wrappers:** Heavy models (DINOv2, SAM, Phi-3-Vision) are loaded behind-the-scenes inside lightweight custom wrappers, keeping the students' environments lightweight and straightforward.

---

## Objectives & Action Items

### 1. Interleaving Pipeline Execution & Curriculum Generation

* **Execution Order Shift:** Modify `run_pipeline.py` to run the ML training, inference, and metrics evaluation *before* the `CurriculumEngine` builds the outputs.

* **Pipeline Metric Injection:** Pass concrete execution statistics (e.g., accuracy, precision, recall, confusion matrix, stage times) into the `CurriculumService` and the renderer.

### 2. Auto-Generation of Weekly Coding Exercises

* **Dynamic Coding Practices:** For weeks that require programming (e.g., preprocessing, train splits, or model evaluation), generate starter templates, solution keys, and unit test suites dynamically.

* **Context Injection:** Populate code templates with pipeline metadata (e.g., actual class names like `['benign', 'malignant']`, image counts, or class imbalance ratios).

### 3. Automated Verification & Validation (Sandbox)

* **Positive Verification (The Solver Test):** Automatically merge the generated *Reference Solution* with the *Unit Tests* and run them in an isolated subprocess. If the tests fail or syntax errors occur, the package is rejected.

* **Negative Verification (The Broken Test):** Merge the generated *Starter Code* with the *Unit Tests* and run them. The tests must fail (e.g., raising `NotImplementedError` or failing assertions). If they pass, the test suite is invalid or trivial.

### 4. Integration: Pipeline as the Source of Truth

* **Dual-Purpose Modules:** Since the active pipeline config loads files like `curriculum_resources.week_08.solution` to execute live stages (classification, segmentation, VQA), these files are inherently the verified "Answer Key".

* **Source-to-Exercise Parsing:** Rather than maintaining duplicate codebases, use a single functional solution file. A compiler script can parse the solution using simple comment tags (e.g., `# [STUDENT_TODO]`) to strip out solutions and auto-generate the `exercise.py` file.
* **Few-Shot LLM Guidance:** When dynamically generating conceptual worksheets or alternative assignments, pass the active, functional pipeline module code to the LLM as the reference context. This guarantees that generated exercises remain strictly aligned with the actual algorithms and data structures processed by the pipeline.

### 5. Interactive ML Playground (Student Interface)

* **Configuration Sandbox:** Build an interactive visual interface (e.g., extending the current Gradio UI) where students can safely adjust hyperparameters (learning rates, batch sizes, epochs, data split ratios) and trigger real-time pipeline execution on small sample batches.

* **LLM Diagnostic Feedback:** Integrate an LLM agent to analyze the student's modified configuration and the resulting run metrics. The LLM provides plain-English diagnostic explanations (e.g., *"Because you increased the learning rate to 0.5, the model's loss exploded and it failed to learn. Try decreasing it to a smaller step size like 0.001 to stabilize training."*).

### 6. Educator Configuration App (Teacher Web App)

* **YAML Configurator UI:** Move away from raw text editing of YAML files (which frequently leads to formatting typos, incorrect schema declarations, or deleted blocks). Build a web-based panel for teachers to:
  * Input basic subject, grade level, and curriculum parameters.
  * Select active pipeline stages (Classification, Segmentation, VQA).
  * Automatically construct and write error-free, validated `config.yaml` files.

### 7. Curriculum Tooling & VQA Strategy

* **Direct PyTorch & OpenCV Modeling:** Instead of hiding machine learning components behind black-box wrapper abstractions, students will interact directly with standard PyTorch and OpenCV APIs to build transferable skills. Coding tasks will guide them through:
  * Loading pretrained backbones (e.g., swapping the final classifier head of a standard `torchvision.models.resnet` or `mobilenet`).
  * Handling image preprocessing, thresholding, contour finding, and mask overlays directly using standard `cv2` (OpenCV) calls.

* **VQA Exercise Design:** For text-based VQA outputs (like Phi-3-Vision diagnostic reasoning), frame student exercises around:
  * **Text Parsing & Scoring:** Writing Python/Regex scripts to scan generated reasoning for clinical keywords (e.g., asymmetry, irregular borders) corresponding to the predicted class.
  * **Prompt Optimization:** Designing and formatting prompt templates to enforce structured outputs (like JSON schemas) from the VQA model.
  * **Overlap Metrics:** Implementing token-level overlap metrics (like Jaccard similarity) to evaluate student explanations against expert labels.

### 8. Deliverables

* **Updated Curriculum Package:** Enriched Markdown and JSON syllabi detailing actual model achievements and pitfalls.

* **Weekly Code Workspace:** A structured directory per week containing:
  * `exercise.py` (Starter code with `# TODO` markers)
  * `test_exercise.py` (Unit tests to run locally)
  * `solution.py` (Educator reference solution)

---

## Example Jinja2 Template: Week 2 Image Preprocessing & Split

To ensure the coding practices are dynamic, we use Jinja2 templates that receive the pipeline's execution config and dataset metrics.

Here is an example template for **Week 2: Train/Validation Splitting and Preprocessing**:

### Template: `exercise_week_2.py.j2`

```python
# =====================================================================
# WEEK 2 EXERCISE: Data Preprocessing & Validation Splitting
# Course: {{ subject }} (Grade {{ grade }})
# Topic: {{ topic_name }}
# Dataset: {{ dataset_name }} ({{ total_images }} images, {{ num_classes }} classes)
# Class Mapping: {{ class_mapping }}
# =====================================================================

import os
import random
from PIL import Image
import torchvision.transforms as transforms

# Define Target Parameters from Pipeline Run
CLASSES = {{ class_mapping | tojson }}
TARGET_SIZE = {{ image_size }}  # Target dimensions for resizing

def get_image_paths(dataset_root):
    """
    Scans the dataset_root and gathers all image files.
    """
    valid_exts = (".jpg", ".jpeg", ".png")
    image_paths = []
    for root, _, files in os.walk(dataset_root):
        for f in files:
            if f.lower().endswith(valid_exts):
                image_paths.append(os.path.join(root, f))
    return image_paths

# ---------------------------------------------------------------------
# TODO: EXERCISE 1 - Preprocessing Transform Pipeline
# Implement a torchvision transform pipeline that:
# 1. Resizes images to TARGET_SIZE x TARGET_SIZE
# 2. Converts them to PyTorch Tensors
# 3. Normalizes them using standard ImageNet mean and std:
#    mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
# ---------------------------------------------------------------------
def get_preprocess_transforms():
    """
    Returns the compiled torchvision.transforms.Compose pipeline.
    """
    # [STUDENT_STARTER]
    # TODO: Implement the transforms pipeline
    # return None
    # [/STUDENT_STARTER]
    # [REFERENCE_SOLUTION]
    return transforms.Compose([
        transforms.Resize((TARGET_SIZE, TARGET_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(
            mean=[0.485, 0.456, 0.406],
            std=[0.229, 0.224, 0.225]
        )
    ])
    # [/REFERENCE_SOLUTION]

# ---------------------------------------------------------------------
# TODO: EXERCISE 2 - Stratified Splitting
# Write a function that splits a list of image paths into train and val
# sets using a specified split ratio. Ensure the split is stratified 
# (preserves class proportions).
# ---------------------------------------------------------------------
def split_dataset(image_paths, train_ratio={{ train_split }}):
    """
    Splits image_paths into train_paths and val_paths.
    Must preserve relative class ratios!
    """
    # Group images by class (extracted from directory path)
    class_groups = {cls: [] for cls in CLASSES}
    for path in image_paths:
        class_name = os.path.basename(os.path.dirname(path))
        if class_name in class_groups:
            class_groups[class_name].append(path)
            
    train_paths = []
    val_paths = []
    
    # [STUDENT_STARTER]
    # TODO: Loop through class_groups, shuffle class images using seed 42,
    # slice them according to train_ratio, and append to train_paths and val_paths.
    # pass
    # [/STUDENT_STARTER]
    # [REFERENCE_SOLUTION]
    random.seed(42)
    for class_name, paths in class_groups.items():
        random.shuffle(paths)
        split_idx = int(len(paths) * train_ratio)
        train_paths.extend(paths[:split_idx])
        val_paths.extend(paths[split_idx:])
    # [/REFERENCE_SOLUTION]
    
    return train_paths, val_paths
```

### Script-based Post-Processing

When the pipeline packages the exercise for the student:

1. It reads the template.
2. It strips out the block between `[REFERENCE_SOLUTION]` and `[/REFERENCE_SOLUTION]` to generate `exercise.py`, leaving the `[STUDENT_STARTER]` contents.
3. It strips out the `[STUDENT_STARTER]` lines to generate `solution.py`, keeping the reference solution.
4. It compiles `test_exercise.py` using a separate test template, verifying both scripts before saving them to disk.

---

## Limitations & Mitigation Strategies

### 1. Verification Sandboxing is Not Security Sandboxing

* **Limitation:** Running scripts with Python's standard `subprocess` module executes code with the same system privileges as the pipeline itself. If there is a major bug in the template or generator (e.g., recursively deleting a directory path resolved to root `/`), it can execute on the host machine.
* **Mitigation:** Since you are writing/templated the scripts rather than letting students submit raw code directly to a live server, this is low-risk. Keep the scope of file modifications in the tests strictly locked to `tempfile.TemporaryDirectory()`.

### 2. High Maintenance of Delimiter Comments

* **Limitation:** Relying on tag comments like `# [REFERENCE_SOLUTION]` and `# [/REFERENCE_SOLUTION]` to parse files is highly sensitive. If you make a typo (e.g., `# [REF_SOLUTION]`), the parsing compiler will break, potentially leaving raw solutions in the student files or stripping out code incorrectly.
* **Mitigation:** Use a robust parsing function that validates that every opening tag in the file has a matching closing tag *before* writing the final files. If tags are unbalanced, throw an explicit compilation error.

### 3. Rigid Test Suites vs. Flexible Coding

* **Limitation:** Unit tests are inherently rigid. If a student solves a problem correctly but uses a slightly different library method (e.g., using `PIL.Image` operations instead of `OpenCV`, or structuring a tensor operation differently), the unit test might fail even though the output is correct.
* **Mitigation:** Test **outcomes**, not implementation details. Instead of testing *how* a student resized an image, test that the resulting tensor has the correct shape `(3, TARGET_SIZE, TARGET_SIZE)` and values bounded between expected ranges. Use tolerances (`torch.allclose` or `math.isclose`) instead of strict equality `==`.

### 4. Brittle VQA Natural Language Verification

* **Limitation:** Trying to grade natural language (VQA reasoning) using regex or Jaccard similarity is notoriously unreliable. A student could write a perfectly valid medical explanation that simply uses synonyms not captured by your keyword dictionary, leading to a false failure.
* **Mitigation:** Use keyword matching only as a "warning" or "suggestion" flag, rather than a hard pass/fail. For grading VQA, focus the tests on checking if the function returns the expected data types and structures, and leave the quality of the explanation to human peer-review or grading keys.
