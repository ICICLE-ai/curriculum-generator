import argparse
from collections import defaultdict
import importlib
import json
import os
import random
import re
import shutil
import time

import torch.multiprocessing as mp
from torch.utils.data import Dataset, DataLoader

from digitalagedu.core import (
    load_config,
    generate_run_report,
    CurriculumEngine,
    DatasetScanner,
)
from digitalagedu.core.progress_tracker import ProgressTracker

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


PHASE1_MARKERS = ("results.csv", "provenance.json", "run_summary.json")


def _resolve_phase1_source(source_dir, output_dir):
    """Finds the Phase 1 output directory containing PHASE1_MARKERS, plus its parent job directory if any."""
    norm_out = os.path.normpath(output_dir)
    if all(os.path.isfile(os.path.join(source_dir, m)) for m in PHASE1_MARKERS):
        abs_out = os.path.abspath(source_dir)
        parent = os.path.dirname(abs_out)
        job_dir = os.path.dirname(parent) if os.path.basename(parent) == "outputs" else None
        return source_dir, job_dir

    candidate = os.path.join(source_dir, norm_out)
    if all(os.path.isfile(os.path.join(candidate, m)) for m in PHASE1_MARKERS):
        return candidate, source_dir

    outputs_root = os.path.join(source_dir, "outputs")
    if os.path.isdir(outputs_root):
        for entry in sorted(os.listdir(outputs_root)):
            sub = os.path.join(outputs_root, entry)
            if os.path.isdir(sub) and all(os.path.isfile(os.path.join(sub, m)) for m in PHASE1_MARKERS):
                return sub, source_dir

    if os.path.isdir(source_dir):
        for entry in sorted(os.listdir(source_dir)):
            sub = os.path.join(source_dir, entry)
            if os.path.isdir(sub) and all(os.path.isfile(os.path.join(sub, m)) for m in PHASE1_MARKERS):
                return sub, source_dir

    raise RuntimeError(f"Phase 1 didn't finish in {source_dir}: no {', '.join(PHASE1_MARKERS)} found")


def stage_phase2_rerun(source_dir, output_dir, config_path, weeks="failed", dest_dir=".", unlock_config=False):
    """Copies a finished run's Phase 1 outputs into dest_dir (the new job's working directory) for Phase 2.
    Copied, not pointed at: generated code reads ./<output_dir>/... relative paths, and Phase 2 rewrites
    provenance.json, which must stay untouched in the original run.
    - When unlock_config=False (rerun mode): locks to the original config hash; weeks="failed" keeps finished weeks.
    - When unlock_config=True (Content Bank mode): bypasses the config hash lock, skips exercises/, and records
      source_bank_dir plus the new configuration_hash in the copied provenance.json."""
    from digitalagedu.core.artifact_validator import compute_file_sha256
    from digitalagedu.core.eval.load import list_finished_weeks

    if weeks not in ("failed", "all"):
        raise ValueError(f"--weeks must be 'failed' or 'all', got {weeks!r}")

    src_out, src_job_dir = _resolve_phase1_source(source_dir, output_dir)
    config_hash = compute_file_sha256(config_path)

    with open(os.path.join(src_out, "provenance.json"), encoding="utf-8") as f:
        prov = json.load(f)
    original_hash = prov.get("configuration_hash")

    if not unlock_config and original_hash and config_hash != original_hash:
        raise RuntimeError(f"{config_path} changed since the original run (its hash no longer matches that run's "
                           "provenance.json). Phase 2 reruns are locked to the original config; submit a new run.")

    if unlock_config:
        weeks = "all"

    abs_src_out = os.path.abspath(src_out)
    dest_out = os.path.join(dest_dir, os.path.normpath(output_dir))

    if src_job_dir is not None and os.path.abspath(src_job_dir) != os.path.abspath(dest_dir):
        abs_job = os.path.abspath(src_job_dir)

        def skip_job(directory, names):
            here = os.path.abspath(directory)
            ignored = []
            if here == abs_job:
                ignored.extend(n for n in names if n.startswith("tapisjob") or n in ("tmp", "outputs"))
            for n in names:
                if os.path.join(here, n) == abs_src_out:
                    ignored.append(n)
            return ignored

        shutil.copytree(src_job_dir, dest_dir, ignore=skip_job, dirs_exist_ok=True)

    if abs_src_out != os.path.abspath(dest_out):
        def skip_exercises(directory, names):
            return ["exercises"] if os.path.abspath(directory) == abs_src_out and "exercises" in names else []

        shutil.copytree(src_out, dest_out, ignore=skip_exercises, dirs_exist_ok=True)

    if unlock_config:
        prov["source_bank_dir"] = abs_src_out
        if original_hash:
            prov["source_configuration_hash"] = original_hash
        prov["configuration_hash"] = config_hash
        with open(os.path.join(dest_out, "provenance.json"), "w", encoding="utf-8") as f:
            json.dump(prov, f, indent=4)

    src_ex = os.path.join(src_out, "exercises")
    dest_ex = os.path.join(dest_out, "exercises")
    kept = []
    if weeks == "failed":
        for name in ("syllabus_plan.json", "course_syllabus.md"):
            if os.path.isfile(os.path.join(src_ex, name)):
                os.makedirs(dest_ex, exist_ok=True)
                shutil.copy2(os.path.join(src_ex, name), dest_ex)
        for week_dir in list_finished_weeks(src_ex):
            rel = os.path.relpath(week_dir, src_ex)
            shutil.copytree(week_dir, os.path.join(dest_ex, rel), dirs_exist_ok=True)
            kept.append(rel)
    mode_label = "Content Bank" if unlock_config else "Phase 2 rerun"
    print(f"[{mode_label}] Copied Phase 1 outputs from {src_out}; weeks={weeks}; "
          f"kept finished: {', '.join(kept) or 'none'}")
    return kept


def _check_refresh_token():
    """Fails in seconds, not after Phase 2 starts, when the job's refresh token has already expired."""
    from digitalagedu.core.llm.rag.qdrant_client import decode_jwt_payload
    token = (os.getenv("TAPIS_REFRESH_TOKEN") or "").strip()
    exp = decode_jwt_payload(token).get("exp") if token else None
    if exp and exp <= time.time():
        raise RuntimeError("The job's TAPIS_REFRESH_TOKEN has expired; log in to the web app again and resubmit.")


def _run_phase2(config_path, output_dir):
    """Phase 2: multi-agent LLM curriculum generation into <output_dir>/exercises, using Phase 1 output as telemetry."""
    print("\n[INFO] Triggering Phase 2 LLM Autonomous Curriculum Generation...")
    from digitalagedu.core.llm import generate_llm_curriculum
    llm_output_dir = os.path.join(output_dir, "exercises")
    generate_llm_curriculum(
        config_path=config_path,
        output_dir=llm_output_dir,
        telemetry_dir=output_dir,
    )
    print(f"[SUCCESS] LLM Curriculum Assets saved to {llm_output_dir}")


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def run_pipeline(config_path, phase="all", from_run=None, weeks="failed", from_bank=None):
    # Load configuration
    config = load_config(config_path)
    output_dir = config.output.directory
    if from_run and from_bank:
        raise ValueError("Pass either --from-run or --from-bank, not both")
    if from_run:
        if phase not in ["2", "llm"]:
            raise ValueError("--from-run reruns Phase 2 only; pass --phase 2")
        _check_refresh_token()
        stage_phase2_rerun(from_run, output_dir, config_path, weeks)  # before the tracker writes progress.json
    elif from_bank:
        if phase not in ["all", "2", "llm"]:
            raise ValueError("--from-bank runs Phase 2 only; pass --phase 2 or omit --phase")
        phase = "2"
        _check_refresh_token()
        stage_phase2_rerun(from_bank, output_dir, config_path, weeks="all", unlock_config=True)
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
                _run_phase2(config_path, output_dir)
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

        # SAMPLE IMAGES: Evenly split max_samples across detected classes
        if config.execution.max_samples is None:
            sample_images = all_images
        else:
            class_to_imgs = defaultdict(list)
            for img_p in all_images:
                cls_name = extract_label_from_path(img_p)
                class_to_imgs[cls_name].append(img_p)

            num_cls = len(classes) if classes else 1
            per_class_quota = max(1, config.execution.max_samples // num_cls)
            remainder = config.execution.max_samples % num_cls

            rng = random.Random(seed)
            sample_images = []
            print(f"[Sampling] Distributing max_samples={config.execution.max_samples} evenly across {num_cls} classes (~{per_class_quota} per class)...")
            for idx, cls_name in enumerate(classes):
                c_imgs = list(class_to_imgs.get(cls_name, []))
                rng.shuffle(c_imgs)
                target_count = per_class_quota + (1 if idx < remainder else 0)
                chosen = c_imgs[:target_count]
                sample_images.extend(chosen)
                print(f"  - Class '{cls_name}': {len(chosen)} / {len(c_imgs)} samples selected")

            rng.shuffle(sample_images)

        print("Processing", len(sample_images), "images...\n")

        tracker.complete_stage("dataset_ingestion", metrics={"total_images": len(all_images), "samples": len(sample_images), "classes": classes})

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

        # Render markdown syllabus using pure-python renderer
        rendered_output = engine.renderer.render(curriculum_output)

        # Save the md syllabus to the ml output folder
        level_slug = re.sub(r"\W+", "_", config.curriculum.level).strip("_")
        curriculum_md_path = os.path.join(output_dir, f"curriculum_{level_slug}.md")
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
        dataset_sample_dir = os.path.join(output_dir, "images", "dataset_sample")
        os.makedirs(raw_dir, exist_ok=True)
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
        if phase == "all" and getattr(config.execution, "use_llm", False):
            tracker.start_stage("exercise_generation", details="Generating weekly coding exercises and lab assets...")
            _run_phase2(config_path, output_dir)
            tracker.complete_stage("exercise_generation")
        elif phase in ["1", "cv"] and getattr(config.execution, "use_llm", False):
            tracker.skip_stage("exercise_generation", reason="Deferred to follow-up Phase 2 CPU job")
        else:
            tracker.skip_stage("exercise_generation", reason="Skipped (use_llm disabled)")

        # -------------------------------------------------------------
        # Stage: Artifact Packaging & Final Reporting
        # -------------------------------------------------------------
        tracker.start_stage("packaging", details="Packaging student requirements.txt and generating telemetry report...")
        from digitalagedu.core.llm.main import STUDENT_REQUIREMENTS  # one list for both requirements.txt files
        requirements_path = os.path.join(output_dir, "requirements.txt")
        with open(requirements_path, "w", encoding="utf-8") as f:
            f.write(STUDENT_REQUIREMENTS)
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
    try:
        mp.set_start_method("spawn", force=True)
    except (RuntimeError, ValueError):
        pass

    parser = argparse.ArgumentParser(description="Run ML Pipeline")
    parser.add_argument("config_path", help="Path to YAML config file")
    parser.add_argument(
        "--phase",
        choices=["all", "1", "2", "cv", "llm"],
        default="all",
        help="Pipeline phase to execute: 1/cv (Vision Models), 2/llm (Multi-Agent LLM), all (Sequential)"
    )
    parser.add_argument("--from-run", default=None,
                        help="Phase 2 rerun: the finished run's job directory, whose Phase 1 outputs are copied here")
    parser.add_argument("--from-bank", default=None,
                        help="Content Bank mode: existing Phase 1 job or output directory to reuse with a new YAML (bypasses config lock)")
    parser.add_argument("--weeks", choices=["failed", "all"], default="failed",
                        help="With --from-run: regenerate only failed/unfinished weeks (default) or all weeks")
    args = parser.parse_args()
    run_pipeline(args.config_path, phase=args.phase, from_run=args.from_run, weeks=args.weeks, from_bank=args.from_bank)