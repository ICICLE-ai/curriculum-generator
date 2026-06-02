import os
import re
import random
import shutil
import csv
from collections import defaultdict
import json
import argparse
from digitalagedu.core.config import load_config
import importlib


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
    parts = path.split(os.sep)
    return parts[-2] if len(parts) >= 2 else "Unknown"
    #return normalize_label(raw)


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run_pipeline(config_path):
    

    # Load configuration
    config = load_config(config_path)

    dataset_root = config.dataset.root_path
    if not dataset_root or not os.path.exists(dataset_root):
        raise ValueError(f"Dataset root not found {dataset_root}")

    classes = [
        d for d in os.listdir(dataset_root)
        if os.path.isdir(os.path.join(dataset_root, d)) and not d.startswith(".")
    ]
    classes.sort()

    # Generate the class mappings
    if config.dataset.save_class_mapping:
        mapping = {str(i): cls_name for i, cls_name in enumerate(classes)}

        output_dir = config.output.directory
        os.makedirs(output_dir, exist_ok=True)

        mapping_path = os.path.join(output_dir, "class_mapping.json")
        with open(mapping_path, "w") as f:
            json.dump(mapping, f, indent=4)
            
        print(f"Class mapping saved to {mapping_path}")



    random.seed(42)

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
    for img_path in sample_images:
        print("=" * 60)
        print("Processing:", img_path)

        ground_truth = extract_label_from_path(img_path)

        # Dynamically build the dictionary as stages

        image_results = {
            "image_path": img_path,
            "ground_truth": ground_truth
        }

        # Iterate through the stages
        for stage in config.pipeline.stages:
            if not stage.active:
                print(f"Skipping {stage.name} (toggled off)")
                continue

            print(f"Running {stage.name}...")

            # load the module file
            module = importlib.import_module(stage.module)

            # call the run_stage function
            stage_output = module.run_stage(img_path, config, stage=stage, previous_results=image_results)

            # Append the module retuned into a final dictionary
            image_results.update(stage_output)
        

        all_results.append(image_results)
        print(f"Final results for {os.path.basename(img_path)}:",image_results)
        

    # -----------------------------
    # FINAL METRICS
    # -----------------------------
    if all_results:
        # Extract every key to use as a csv column
        fieldnames = set()
        for res in all_results:
            fieldnames.update(res.keys())

        # Write to the csv
        with open(results_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(fieldnames))
            writer.writeheader()
            writer.writerows(all_results)




    print("\nPipeline completed successfully")
    print("Results saved in:", output_dir)


    return "Pipeline completed"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ML Pipeline")
    parser.add_argument("config_path", help="Path to YAML config file")
    args = parser.parse_args()
    run_pipeline(args.config_path)