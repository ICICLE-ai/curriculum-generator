from digitalagedu.core.dataset_registry import DATASET_REGISTRY
from digitalagedu.core.learning_outcomes_service import LearningOutcomesService
import math
import json
from pathlib import Path

MIN_WEEKS = 4
MAX_WEEKS = 24
RESOURCES_FOLDER = Path("curriculum_resources")


class CurriculumService:
    def __init__(self, config, dynamic_weeks: bool = True):
        self.config = config
        self.dynamic_weeks = dynamic_weeks

    def build(self, pipeline_metrics = None):
        curriculum = self.config.curriculum
        lo_service = LearningOutcomesService()

        # --- Process Pipeline Metrics ----
        processed_metrics = {}
        if pipeline_metrics:
            results = pipeline_metrics.get("results", [])
            stage_times = pipeline_metrics.get("stage_times", {})

            correct = 0
            total = len(results)
            correct_samples = []
            misclassified_samples = []

            for r in results:
                # Get the ground truth and predicted labals
                gt = r.get("ground_truth", "Unknown")
                pred = r.get("predicted_class", r.get("prediction", "Unkown"))

                # Check prediction success
                if str(gt).lower() == str(pred).lower():
                    correct += 1
                    if len(correct_samples) < 3:
                        correct_samples.append({
                            "path": r.get("image_path"),
                            "ground_truth": gt,
                            "predicted": pred
                        })
                else:
                    if len(misclassified_samples) < 3:
                        misclassified_samples.append({
                        "path": r.get("image_path"),
                        "ground_truth": gt,
                        "predicted": pred 
                        })
            accuracy = (correct / total) if total > 0 else 0.0
            processed_metrics = {
                "total_samples": total,
                "accuracy": round(accuracy * 100, 2),
                "stage_times": stage_times,
                "correct_samples": correct_samples,
                "misclassified_samples": misclassified_samples
            }

        # Step 1 – Determine total weeks
        if getattr(curriculum, "weeks", None) is not None:
            total_weeks = curriculum.weeks
        else:
            total_weeks = self._estimate_weeks(curriculum.topics)
        total_weeks = max(MIN_WEEKS, min(MAX_WEEKS, total_weeks))

        topics_output = []
        for topic in curriculum.topics:
            activities = self._generate_activities(topic, total_weeks)
            week_distribution = self._distribute_activities(activities, total_weeks)

            # Attach resources only for weeks generated
            resources = self._attach_resources(topic, total_weeks)

            # ---------------------------
            # NEW: Generate Learning Outcomes
            # ---------------------------
            learning_outcomes = lo_service.generate(
                {
                    "dataset_metadata": getattr(topic, "dataset_metadata", {}),
                },
                week_distribution
            )

            topic_dict = {
                "name": topic.name,
                "description": topic.description,
                "project": topic.project,
                "dataset_metadata": getattr(topic, "dataset_metadata", None),
                "weeks": week_distribution,
                "resources": resources,
                "activities": activities,
                "learning_outcomes": learning_outcomes,
            }

            topics_output.append(topic_dict)

        global_resources = getattr(curriculum, "resources", None) or []
        
        return {
            "subject": curriculum.subject,
            "grade": curriculum.grade,
            "weeks": total_weeks,
            "global_resources": [r.model_dump() for r in global_resources],

            # Prerequisites (existing)
            "prerequisites": {
                "path": str(RESOURCES_FOLDER / "prerequisites" / "README.md"),
                "estimated_time": "45-60 minutes"
            },

            # Explore More Models (existing)
            "explore_more_models": {
                "path": str(RESOURCES_FOLDER / "prerequisites" / "models" / "README.md"),
                "note": "Optional: Explore additional AI models for classification, segmentation, and vision-language tasks."
            },

            "topics": topics_output,
            "pipeline_metrics": processed_metrics
        }

    # ---------------------------
    # Estimate total weeks dynamically
    # ---------------------------
    def _estimate_weeks(self, topics):
        total_weeks = 0
        for topic in topics:
            meta = getattr(topic, "dataset_metadata", None)
            if meta:
                num_classes = meta.get("num_classes", 2)
                total_images = meta.get("total_images", 1000)
                imbalance = meta.get("imbalance_ratio", 1)
                weeks = math.ceil((num_classes * 0.5 + total_images / 5000 + imbalance / 3))
            else:
                weeks = 2
            total_weeks = max(total_weeks, weeks)
        return max(MIN_WEEKS, min(MAX_WEEKS, total_weeks))

    # ---------------------------
    # Generate activities for a topic
    # ---------------------------
    def _generate_activities(self, topic, total_weeks):
        activities = []

        context_statement = self.config.project.context_statement
        
        # ----------------------------------------------------
        # TIER 1: Core Fundamentals (Always included, even in 4 weeks)
        # ----------------------------------------------------
        if topic.dataset_metadata:
            activities.append(f"Explore dataset directory structure and perform NumPy Basics array calculations and Z-score matrix normalization for {topic.name}.")
            activities.append("Perform Pandas & Matplotlib data analysis and plot distribution charts on pipeline results.csv.")
            activities.append("Implement Deep Learning Foundations: build an MLP classifier, compute Cross-Entropy Loss, and train with the Adam optimizer.")
            activities.append("Build an interactive image segmentation application with OpenCV using mouse callbacks and compute IoU against SAM.")

        # ----------------------------------------------------
        # TIER 2: Intermediate CV (Unlocked at 8+ weeks)
        # ----------------------------------------------------
        if total_weeks >= 8 and topic.dataset_metadata:
            activities.append("Build PyTorch Datasets & DataLoaders to load image batches and benchmark disk I/O performance.")
            activities.append("Design custom convolutional neural networks (CNNs) and extract intermediate feature maps.")
            activities.append("Tune cnn optimization, regularization & checkpointing using BatchNorm, Dropout, and schedulers.")
            activities.append("Perform transfer learning & backbone benchmarking by fine-tuning ResNet18 and comparing it against DINOv2.")

        # ----------------------------------------------------
        # TIER 3: Advanced Deep Vision (Unlocked at 16+ weeks)
        # ----------------------------------------------------
        if total_weeks >= 16 and topic.dataset_metadata:
            activities.append("Build a deep learning semantic segmentation & u-net architecture to predict pixel-wise target masks.")
            activities.append("Debug classification decisions using explainable ai & grad-cam visual attention overlays.")
            activities.append("Explore image embeddings, clustering & semantic search by projecting DINOv2 vectors.")

        # ----------------------------------------------------
        # TIER 4: Deployment (Unlocked at 24+ weeks)
        # ----------------------------------------------------
        if total_weeks >= 24 and topic.dataset_metadata:
            activities.append("Deploy a multi-stage capstone integration & gradio deployment application.")

        return activities

    # ---------------------------
    # Split activities across weeks
    # ---------------------------
    def _distribute_activities(self, activities, total_weeks):
        n = len(activities)
        week_distribution = {}

        if total_weeks == 24 and n == 12:
            # Explicitly match the approved 24-week schedule without VLM
            durations = [1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 4]
            current_week = 1
            for act, dur in zip(activities, durations):
                if dur == 4:
                    week_name = f"Week_{current_week:02d}_{(current_week + 3):02d}"
                    current_week += 4
                elif dur == 3:
                    week_name = f"Week_{current_week:02d}_{(current_week + 2):02d}"
                    current_week += 3
                elif dur == 2:
                    week_name = f"Week_{current_week:02d}_{(current_week + 1):02d}"
                    current_week += 2
                else:
                    week_name = f"Week_{current_week:02d}"
                    current_week += 1
                week_distribution[week_name] = [act]
                
        elif total_weeks == 16 and n == 11:
            # Match 16-week schedule
            durations = [1, 1, 2, 1, 2, 2, 2, 1, 1, 1, 2]
            current_week = 1
            for act, dur in zip(activities, durations):
                if dur == 2:
                    week_name = f"Week_{current_week:02d}_{(current_week + 1):02d}"
                    current_week += 2
                else:
                    week_name = f"Week_{current_week:02d}"
                    current_week += 1
                week_distribution[week_name] = [act]
                
        else:
            # Fallback when total_weeks < n or other configurations: group activities sequentially
            week_distribution = {f"Week_{i:02d}": [] for i in range(1, total_weeks + 1)}
            base_size = n // total_weeks
            remainder = n % total_weeks
            
            current_idx = 0
            for i in range(1, total_weeks + 1):
                size = base_size + (1 if i <= remainder else 0)
                week_distribution[f"Week_{i:02d}"] = activities[current_idx:current_idx + size]
                current_idx += size

        return week_distribution

    # ---------------------------
    # Attach resources and starter code
    # ---------------------------
    def _attach_resources(self, topic, total_weeks):
        """
        Attach dataset + resource metadata.
        Resources are global (not topic-specific), so we only attach the root path.
        """

        meta = getattr(topic, "dataset_metadata", None) or {}

        resources_output = {
            "dataset_root": meta.get("dataset_path", ""),
            "resources_root": str(RESOURCES_FOLDER),
            "pipeline_entry": "Code/run_pipeline.py"
        }

        return resources_output