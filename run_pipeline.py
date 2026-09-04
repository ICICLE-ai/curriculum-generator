import argparse
from collections import defaultdict
import csv
import importlib
import json
import os
import random
import re
import shutil
import time

import torch
import torch.multiprocessing as mp
from torch.utils.data import Dataset, DataLoader

from digitalagedu.core import (
    load_config,
    generate_run_report,
    CurriculumEngine,
    CurriculumService,
    TemplateRenderer,
    DatasetScanner,
)
from digitalagedu.core.progress_tracker import ProgressTracker



# -----------------------------
# GLOBAL CONFIG
# -----------------------------
CHECKPOINT_PATH = "week8_dinov2_finetuned.pth"

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
def run_pipeline(config_path, phase="all"):
    # Load configuration
    config = load_config(config_path)
    output_dir = config.output.directory
    os.makedirs(output_dir, exist_ok=True)

    # Initialize dynamic progress tracker
    tracker = ProgressTracker(
        output_dir=output_dir,
        stages_config=getattr(config.pipeline, "stages", []) if hasattr(config, "pipeline") else []
    )

    try:
        # Direct Phase 2 Dispatch (when running standalone Phase 2 after vLLM startup)
        if phase in ["2", "llm"]:
            tracker.start_stage("curriculum_synthesis", details="Triggering Phase 2 LLM Autonomous Curriculum Generation...")
            if getattr(config.execution, "use_llm", False):
                print("\n[INFO] Triggering Phase 2 LLM Autonomous Curriculum Generation...")
                try:
                    from digitalagedu.core.llm import generate_llm_curriculum
                    llm_output_dir = os.path.join(output_dir, "exercises")
                    generate_llm_curriculum(
                        config_path=config_path,
                        output_dir=llm_output_dir,
                        telemetry_dir=output_dir,
                        base_url=getattr(config.execution, "llm_base_url", "http://localhost:8000/v1"),
                        model_name=getattr(config.execution, "llm_model", "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ")
                    )
                    print(f"[SUCCESS] LLM Curriculum Assets saved to {llm_output_dir}")
                except Exception as e:
                    print(f"[WARNING] Phase 2 LLM Generation failed: {e}")
            tracker.complete_stage("curriculum_synthesis")
            tracker.finish_all()
            print("\nPhase 2 completed successfully")
            print("Results saved in:", output_dir)
            return "Phase 2 completed"

        # Start timer for Phase 1
        start_time = time.time()

        # Generate the seed for the entire run
        if config.execution.seed is None:
            config.execution.seed = random.randint(1,100000)

        seed = config.execution.seed
        print(f"\n[INFO] Seed set to {seed}")

        # Stage 1: Dataset Ingestion
        tracker.start_stage("dataset_ingestion", details="Scanning dataset root and discovering classes...")

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

        # COLLECT IMAGES
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

        # SAMPLE IMAGES
        if config.execution.max_samples is None:
            sample_images = all_images
        else:
            sample_images = random.sample(all_images, min(config.execution.max_samples, len(all_images)))

        print("Processing", len(sample_images), "images...\n")

        tracker.complete_stage("dataset_ingestion", metrics={"total_images": len(all_images), "samples": len(sample_images), "classes": classes})

        # METRICS TRACKING
        correct = 0
        total = 0
        confusion = defaultdict(lambda: defaultdict(int))

        # PROCESS IMAGES (Dynamic Granular ML Stages)
        all_results = []
        
        # Initialize the DataLoader
        dataset = ImagePathDataset(sample_images)
        dataloader = DataLoader(
            dataset,
            batch_size = config.execution.batch_size,
            num_workers = 1,
            shuffle = False
        )
        total_batches = len(dataloader)
        stage_times = defaultdict(float)

        # Loop each batch
        for batch_idx, batch_paths in enumerate(dataloader):
            print("=" * 60)
            print(f"Processing Batch {batch_idx + 1}/{total_batches} ({len(batch_paths)} images)...")

            # Initialize the results for the batch
            batch_results = []
            for img_path in batch_paths:
                batch_results.append({
                    "image_path" : str(img_path),
                    "ground_truth" : extract_label_from_path(str(img_path))
                })
            
            # Run the entire batch through each dynamic pipeline stage
            for stage in config.pipeline.stages:
                if not stage.active:
                    print(f"Skipping {stage.name}...")
                    continue
                
                tracker.update_stage_progress(
                    stage.name,
                    current=batch_idx + 1,
                    total=total_batches,
                    message=f"Processing batch {batch_idx + 1}/{total_batches} ({len(batch_paths)} images)"
                )
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

        # Mark all active ML stages as COMPLETED
        for stage in config.pipeline.stages:
            if stage.active:
                tracker.complete_stage(stage.name, metrics={"duration_hours": round(stage_times[stage.name] / 3600, 4)})

        #---------------------------------
        # Generate Curriculum and Syllabus
        #---------------------------------
        print("\n[INFO] Generating curriculum artifacts")
        tracker.start_stage("curriculum_synthesis", details="Building lesson plans and JSON curriculum...")
        
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
        grade_str = str(getattr(config.curriculum, "grade", None) or getattr(config.curriculum, "target_level", None) or "10").replace(" ", "_").replace("/", "_")
        curriculum_md_path = os.path.join(output_dir, f"curriculum_grade_{grade_str}.md")
        engine.writer.write(rendered_output, curriculum_md_path)
        tracker.complete_stage("curriculum_synthesis")

        # -------------------------------------------------------------
        # Generate Run Report & Stage Authentic Image Assets for Labs
        # -------------------------------------------------------------
        if all_results:
            stage_time_hours = {k : round(v/3600, 2) for k, v in stage_times.items()}
            generate_run_report(all_results, start_time, config_path, output_dir, seed, stage_time_hours)

        # Stage authentic sample images and mini-datasets for self-contained student exercises
        raw_dir = os.path.join(output_dir, "images", "raw")
        mask_dir = os.path.join(output_dir, "images", "masks")
        dataset_sample_dir = os.path.join(output_dir, "images", "dataset_sample")
        os.makedirs(raw_dir, exist_ok=True)
        os.makedirs(mask_dir, exist_ok=True)
        os.makedirs(dataset_sample_dir, exist_ok=True)

        # Find representative paired sample image and mask
        orig_sample_image_path = ""
        orig_sample_mask_path = ""
        if all_results:
            for res in all_results:
                img_p = res.get("image_path")
                mask_p = res.get("mask_path") or res.get("segmented_mask_path") or res.get("mask")
                if img_p and mask_p and os.path.exists(str(img_p)) and os.path.exists(str(mask_p)):
                    orig_sample_image_path = str(img_p)
                    orig_sample_mask_path = str(mask_p)
                    break
            if not orig_sample_image_path:
                for res in all_results:
                    if res.get("image_path") and os.path.exists(str(res["image_path"])):
                        orig_sample_image_path = str(res["image_path"])
                        break

        if orig_sample_image_path and os.path.exists(orig_sample_image_path):
            sample_img_basename = os.path.basename(orig_sample_image_path)
            try:
                shutil.copy2(orig_sample_image_path, os.path.join(raw_dir, sample_img_basename))
            except Exception:
                pass

        if orig_sample_mask_path and os.path.exists(orig_sample_mask_path):
            mask_basename = os.path.basename(orig_sample_mask_path)
            try:
                shutil.copy2(orig_sample_mask_path, os.path.join(mask_dir, mask_basename))
            except Exception:
                pass

        # Stage up to 500 images across classes for dataset-level exercises
        total_target_samples = 500
        per_class_limit = max(1, total_target_samples // len(classes)) if classes else 250
        for cls in classes:
            cls_sample_dir = os.path.join(dataset_sample_dir, cls)
            os.makedirs(cls_sample_dir, exist_ok=True)
            src_cls_dir = os.path.join(dataset_root, cls)
            if os.path.exists(src_cls_dir):
                class_files = [f for f in os.listdir(src_cls_dir) if f.lower().endswith(valid_ext)]
                for cf in class_files[:per_class_limit]:
                    try:
                        shutil.copy2(os.path.join(src_cls_dir, cf), os.path.join(cls_sample_dir, cf))
                    except Exception:
                        pass

        # -------------------------------------------------------------
        # Phase 2: Exercise Generation / LLM Curriculum
        # -------------------------------------------------------------
        tracker.start_stage("exercise_generation", details="Generating weekly coding exercises and lab assets...")
        if phase == "all" and getattr(config.execution, "use_llm", False):
            print("\n[INFO] Triggering Phase 2 LLM Autonomous Curriculum Generation...")
            try:
                from digitalagedu.core.llm import generate_llm_curriculum
                llm_output_dir = os.path.join(output_dir, "exercises")
                generate_llm_curriculum(
                    config_path=config_path,
                    output_dir=llm_output_dir,
                    telemetry_dir=output_dir,
                    base_url=getattr(config.execution, "llm_base_url", "http://localhost:8000/v1"),
                    model_name=getattr(config.execution, "llm_model", "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ")
                )
                print(f"[SUCCESS] LLM Curriculum Assets saved to {llm_output_dir}")
            except Exception as e:
                print(f"[WARNING] Phase 2 LLM Generation failed: {e}")
        tracker.complete_stage("exercise_generation")

        # -------------------------------------------------------------
        # Stage: Artifact Packaging & Final Reporting
        # -------------------------------------------------------------
        tracker.start_stage("packaging", details="Packaging student requirements.txt and generating telemetry report...")
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
            "scikit-image>=0.21\n"
            "scipy>=1.10\n"
            "timm>=0.9\n"
            "segment-anything>=1.0\n"
        )
        with open(requirements_path, "w", encoding="utf-8") as f:
            f.write(student_requirements)
        print(f"[SUCCESS] Packaged student requirements.txt to {requirements_path}")
        tracker.complete_stage("packaging")
        tracker.finish_all(final_metrics={"total_samples": len(all_results)})

        print("\nPipeline completed successfully")
        print("Results saved in:", output_dir)
        return "Pipeline completed"

    except Exception as e:
        current_stg = tracker.current_stage_id or "pipeline"
        tracker.fail_stage(current_stg, str(e))
        print(f"\n[ERROR] Pipeline failed during {current_stg}: {e}")
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ML Pipeline")
    parser.add_argument("config_path", help="Path to YAML config file")
    parser.add_argument(
        "--phase",
        choices=["all", "1", "2", "cv", "llm"],
        default="all",
        help="Pipeline phase to execute: 1/cv (Vision Models), 2/llm (Multi-Agent LLM), all (Sequential)"
    )
    args = parser.parse_args()
    run_pipeline(args.config_path, phase=args.phase)