import os
import re
import random
import shutil
import csv
from collections import defaultdict
import json
import argparse
from digitalagedu.core.config import load_config
from digitalagedu.core.metrics import generate_run_report
import importlib
import time
from torch.utils.data import Dataset, DataLoader
import random

# Parallel processing
import torch.multiprocessing as mp
try:
    mp.set_start_method('spawn', force=True)
except RuntimeError:
    pass

# Generate the curriclum/syllabus
from digitalagedu.core.orchestrator import CurriculumEngine
from digitalagedu.core.curriculum_service import CurriculumService
from digitalagedu.core.renderer import TemplateRenderer
from digitalagedu.core.dataset_scanner import DatasetScanner

# Create practices and exercises
from digitalagedu.core.practice_generator import PracticeGenerator



# -----------------------------
# GLOBAL CONFIG
# -----------------------------
CHECKPOINT_PATH = "week8_dinov2_finetuned.pth"





# -----------------------------
# HELPER: Normalize label
# -----------------------------
# def normalize_label(raw_label):
#     """
#     Maps a raw folder name to the nearest canonical class name.

#     Strategy (applied in order):
#     1. Strip trailing date/numeric suffixes (e.g. _8_31_2017, _7_1_2019)
#     2. Normalize whitespace and casing
#     3. Find the best matching canonical class via substring or token overlap
#     4. Fall back to the cleaned string if no match is found
#     """
#     # Step 1: strip trailing _digits patterns (dates, IDs, version numbers)
#     cleaned = re.sub(r'(_\d+)+$', '', raw_label).strip()

#     # Step 2: normalize casing and whitespace
#     cleaned = ' '.join(cleaned.split())

#     # Step 3: exact match (case-insensitive)
#     for cls in KNOWN_CLASSES:
#         if cleaned.lower() == cls.lower():
#             return cls

#     # Step 4: canonical class is substring of cleaned label (or vice versa)
#     for cls in KNOWN_CLASSES:
#         if cls.lower() in cleaned.lower() or cleaned.lower() in cls.lower():
#             return cls

#     # Step 5: token overlap — pick class with most words in common
#     cleaned_tokens = set(cleaned.lower().split())
#     best_match = None
#     best_score = 0
#     for cls in KNOWN_CLASSES:
#         cls_tokens = set(cls.lower().split())
#         score = len(cleaned_tokens & cls_tokens)
#         if score > best_score:
#             best_score = score
#             best_match = cls

#     if best_match and best_score > 0:
#         return best_match

#     # Step 6: no match found — return cleaned string as-is
#     return cleaned


# -----------------------------
# HELPER: Extract Ground Truth
# -----------------------------
def extract_label_from_path(path):
    """
    Assumes folder structure:
    .../ClassName/.../image.jpg
    """
    # Normalize to forward slashes to handle both Windows and Linux paths
    parts = str(path).replace("\\", "/").split("/")
    return parts[-2] if len(parts) >= 2 else "Unknown"
    #return normalize_label(raw)


# -----------------------------
# PyTorch Dataset for Multiprocessing Pickling
# -----------------------------
class ImagePathDataset(Dataset):
    def __init__(self, paths):
        self.paths = paths

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, idx):
        return self.paths[idx]


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run_pipeline(config_path):
    # Start timer
    start_time = time.time()

    # Load configuration
    config = load_config(config_path)

    # Generate the seed for the entire run
    if config.execution.seed is None:
        config.execution.seed = random.randint(1,100000)

    seed = config.execution.seed
    print(f"\n[INFO] Seed set to {seed}")


    dataset_root = config.dataset.root_path
    if not dataset_root or not os.path.exists(dataset_root):
        raise ValueError(f"Dataset root not found {dataset_root}")

    classes = [
        d for d in os.listdir(dataset_root)
        if os.path.isdir(os.path.join(dataset_root, d)) and not d.startswith(".")
    ]
    classes.sort()

    if not classes:
        raise ValueError(f"No class subdirectories found in dataset root: {dataset_root}")

    # Define and create output directory
    output_dir = config.output.directory
    os.makedirs(output_dir, exist_ok=True)

    # Generate the class mappings
    if config.dataset.save_class_mapping:
        mapping = {str(i): cls_name for i, cls_name in enumerate(classes)}

        mapping_path = os.path.join(output_dir, "class_mapping.json")
        with open(mapping_path, "w") as f:
            json.dump(mapping, f, indent=4)
            
        print(f"Class mapping saved to {mapping_path}")

    random.seed(seed)



    print("\nStarting AI Pipeline")


    images_dir = os.path.join(output_dir, "images")
    segmented_dir = os.path.join(images_dir, "segmented")
    mask_dir = os.path.join(images_dir, "masks")

    os.makedirs(segmented_dir, exist_ok=True)
    os.makedirs(mask_dir, exist_ok=True)

    results_file = os.path.join(output_dir, "results.csv")

    

    
    # -----------------------------
    # COLLECT IMAGES
    # -----------------------------
    valid_ext = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
    all_images = []

    for root, _, files in os.walk(dataset_root):
        # Ignore train and test folders for now
        if "train" in root.split(os.sep) or "test" in root.split(os.sep):
            continue
        for f in files:
            if f.lower().endswith(valid_ext):
                all_images.append(os.path.join(root, f))

    if not all_images:
        raise RuntimeError("No images found in dataset")

    print("\nTotal images found:", len(all_images))

    # -----------------------------
    # SAMPLE IMAGES
    # -----------------------------

    if config.execution.max_samples is None:
        sample_images = all_images
    else:
        sample_images = random.sample(all_images, min(config.execution.max_samples, len(all_images)))

    print("Processing", len(sample_images), "images...\n")

    # -----------------------------
    # METRICS TRACKING
    # -----------------------------
    correct = 0
    total = 0
    confusion = defaultdict(lambda: defaultdict(int))



    # -----------------------------
    # PROCESS IMAGES
    # -----------------------------
    all_results = []
    

    # Initialize the DataLoader
    dataset = ImagePathDataset(sample_images)
    dataloader = DataLoader(
        dataset,
        batch_size = config.execution.batch_size,
        num_workers = 1,
        shuffle = False
    )
    stage_times = defaultdict(float)

    # Loop each batch
    for batch_paths in dataloader:
        print("=" * 60)
        print(f"Processing Batch of {len(batch_paths)} images...")

        # Initialize the results for the batch
        batch_results = []
        for img_path in batch_paths:
            batch_results.append({
                "image_path" : str(img_path),
                "ground_truth" : extract_label_from_path(str(img_path))
            })
        
        # Run the entie batch through the pipeline stages
        for stage in config.pipeline.stages:
            if not stage.active:
                print(f"Skipping {stage.name}...")
                continue
            print(f"Running {stage.name} on batch...")
            module = importlib.import_module(stage.module)

            # Start stopwatch
            start_stage_time = time.time()

            # Call run_batch
            stage_output_list = module.run_batch(batch_paths, config, stage = stage, previous_results_list=batch_results)

            # Stop stopwatch
            stage_times[stage.name] += time.time() - start_stage_time

            # Merge the batch outputs into the tracking dict
            for i, result_dict in enumerate(stage_output_list):
                batch_results[i].update(result_dict)
        
        # Append the finished batch to final list
        all_results.extend(batch_results)
        print("Batch Complete!")

    #---------------------------------
    # Generate Curriculum and Syllabus
    #---------------------------------
    print("\n[INFO] Generating curriculum artifacts")
    
    # Init the core engine
    engine = CurriculumEngine(config_path)

    # Scan the dataset path dynamically
    scanner = DatasetScanner(config.dataset.root_path)
    metadata = scanner.scan()

    # Attach the metadata to the  engines' config topics
    for topic in engine.config.curriculum.topics:
        topic.dataset_metadata = metadata.model_dump()

    # Transform config into dict
    stage_time_hours = {k: round(v / 3600, 4) for k, v in stage_times.items()}
    curriculum_output = engine.service.build(
        pipeline_metrics = {
            "stage_times" : stage_time_hours,
            "results" : all_results
        }
    )

    # Output the JSON to the output folder
    curriculum_json_path = os.path.join(output_dir,"curriculum.json")
    with open(curriculum_json_path, "w") as f:
        json.dump(curriculum_output, f, indent=4)
    print(f"[SUCCESS] JSON Curriculum saved to {curriculum_json_path}")

    rendered_output = engine.renderer.render(
        template_name="lesson_plan.md.j2",
        context=curriculum_output
    )

    # Save the md syllabus to the ml output folder
    curriculum_md_path = os.path.join(output_dir,f"curriculum_grade_{config.curriculum.grade}.md")
    engine.writer.write(rendered_output, curriculum_md_path)

    # --------------------------
    # Generate Weekly Exercises
    # --------------------------
    exercise_start_time = time.time()
    

    # Find sample paths for student exercises
    sample_image_path = ""
    sample_mask_path = ""
    if all_results:
        for res in all_results:
            if res.get("image_path"):
                sample_image_path = res["image_path"]
            if res.get("mask_path"):
                sample_mask_path = res["mask_path"]
            elif res.get("segmented_mask_path"):
                sample_mask_path = res["segmented_mask_path"]
            elif res.get("mask"):
                sample_mask_path = res["mask"]
            if sample_image_path and sample_mask_path:
                sample_mask_path = f"../../../images/masks/{os.path.basename(sample_mask_path)}"
                break

    # Create the template context from the config
    exercise_context = {
        "subject": curriculum_output.get("subject", "AI Curriculum"),
        "grade": curriculum_output.get("grade", 10),
        "class_mapping": classes,
        "image_size": config.execution.image_size,
        "train_split": config.dataset.train_split,
        "dataset_root": config.dataset.root_path,
        "sample_image_path": sample_image_path,
        "sample_mask_path": sample_mask_path
    }

    # Path to your templates directory
    templates_dir = os.path.join(os.path.dirname(__file__), "digitalagedu", "templates")
    
    practice_gen = PracticeGenerator(
        templates_dir=templates_dir,
        output_dir=output_dir,
        config=config
    )

    # Iterate through each topic in the curriculum to process its weeks
    for topic_dict in curriculum_output.get("topics", []):
        week_dist = topic_dict.get("weeks", {})
        practice_gen.generate(week_dist, exercise_context)

    stage_times["Exercise Generation"] = time.time() - exercise_start_time

    # Package requirements.txt to output root folder
    requirements_path = os.path.join(output_dir, "requirements.txt")
    student_requirements = (
        "numpy>=1.24\n"
        "pandas>=2.0\n"
        "matplotlib>=3.7\n"
        "seaborn>=0.13\n"
        "pillow>=10.0\n"
        "opencv-python>=4.8\n"
        "gradio>=4.0\n"
        "torch>=2.0\n"
        "torchvision>=0.15\n"
        "scikit-learn>=1.0\n"
        "timm>=0.9\n"
        "segment-anything>=1.0\n"
        "jinja2>=3.0\n"
        "pyyaml>=6.0\n"
    )
    with open(requirements_path, "w", encoding="utf-8") as f:
        f.write(student_requirements)
    print(f"[SUCCESS] Packaged student requirements.txt to {requirements_path}")

    # ----------------------------------
    # Convert stage times and log report
    # ----------------------------------
    if all_results:
        stage_time_hours = {k : round(v/3600, 2) for k, v in stage_times.items()}
        generate_run_report(all_results, start_time, config_path, output_dir, seed, stage_time_hours)


    print("\nPipeline completed successfully")
    print("Results saved in:", output_dir)


    return "Pipeline completed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ML Pipeline")
    parser.add_argument("config_path", help="Path to YAML config file")
    args = parser.parse_args()
    run_pipeline(args.config_path)