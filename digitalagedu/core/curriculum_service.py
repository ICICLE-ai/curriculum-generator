from digitalagedu.core.dataset_registry import DATASET_REGISTRY
from digitalagedu.core.learning_outcomes_service import LearningOutcomesService
import math
import json
from pathlib import Path

MIN_WEEKS = 4
MAX_WEEKS = 16
RESOURCES_FOLDER = Path("curriculum_resources")


class CurriculumService:
    def __init__(self, config, dynamic_weeks: bool = True):
        self.config = config
        self.dynamic_weeks = dynamic_weeks

    def build(self):
        curriculum = self.config.curriculum
        lo_service = LearningOutcomesService()

        # Step 1 – Determine total weeks
        total_weeks = self._estimate_weeks(curriculum.topics)
        total_weeks = max(MIN_WEEKS, min(MAX_WEEKS, total_weeks))

        topics_output = []
        for topic in curriculum.topics:
            activities = self._generate_activities(topic)
            week_distribution = self._distribute_activities(activities, total_weeks)

            # Attach resources only for weeks generated
            resources = self._attach_resources(topic, total_weeks)

            # ---------------------------
            # NEW: Generate Learning Outcomes
            # ---------------------------
            learning_outcomes = lo_service.generate(
                {
                    "dataset_metadata": getattr(topic, "dataset_metadata", {})
                },
                activities
            )

            topic_dict = {
                "name": topic.name,
                "description": topic.description,
                "project": topic.project,
                "dataset_metadata": getattr(topic, "dataset_metadata", None),
                "weeks": week_distribution,
                "resources": resources,
                "activities": activities,

                # NEW FIELD
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
    def _generate_activities(self, topic):
        activities = []

        # Week 1 – Context
        context_statement = self.config.project.context_statement
        activities.append(f"Introduction to {topic.name} and its role in {context_statement}")

        if topic.dataset_metadata:
            meta = topic.dataset_metadata
            classes = meta.get("num_classes", 0)
            images = meta.get("total_images", 0)
            imbalance = meta.get("imbalance_ratio", 0)
            difficulty = meta.get("difficulty_level", "intermediate")

            # Data Understanding
            activities.append("Explore dataset directory structure and labeling format.")
            activities.append(f"Perform exploratory data analysis on {images} images across {classes} classes.")
            activities.append("Visualize class distribution using charts.")

            # Imbalance Handling
            if imbalance > 3:
                activities.append("Understand class imbalance and its impact on model bias.")
                activities.append("Apply resampling or data augmentation strategies.")

            # Preprocessing
            activities.append("Implement image preprocessing and normalization.")
            activities.append("Split dataset into train, validation, and test sets.")

            # Modeling
            activities.append("Train baseline classification model.")
            activities.append("Evaluate model using suggested metrics.")
            activities.append("Analyze confusion matrix and misclassifications.")

            # Advanced Topics
            if difficulty == "advanced":
                activities.append("Experiment with transfer learning models.")
                activities.append("Perform hyperparameter tuning.")
                activities.append("Compare multiple model architectures.")

        # Finalization
        activities.append("Final project implementation and presentation.")
        activities.append("Reflection, limitations, and ethical AI discussion.")

        return activities

    # ---------------------------
    # Split activities across weeks
    # ---------------------------
    def _distribute_activities(self, activities, total_weeks):
        week_distribution = {f"Week {i}": [] for i in range(1, total_weeks + 1)}

        # Evenly distribute activities
        for idx, activity in enumerate(activities):
            week_number = (idx % total_weeks) + 1
            week_distribution[f"Week {week_number}"].append(activity)

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