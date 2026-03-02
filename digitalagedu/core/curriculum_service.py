from digitalagedu.core.dataset_registry import DATASET_REGISTRY
import math

MIN_WEEKS = 4
MAX_WEEKS = 16

class CurriculumService:
    def __init__(self, config, dynamic_weeks: bool = False):
        self.config = config
        self.dynamic_weeks = dynamic_weeks

    def build(self):
        curriculum = self.config.curriculum

        # Determine total weeks
        # First estimate from dataset
        if not self.dynamic_weeks and curriculum.weeks is not None:
            total_weeks = curriculum.weeks
        else:
            total_weeks = self._estimate_weeks(curriculum.topics)

        # Now adjust weeks based on activity depth
        max_activity_weeks = 0

        for topic in curriculum.topics:
            activities = self._generate_activities(topic)
            max_activity_weeks = max(max_activity_weeks, len(activities))

        # Final weeks should not exceed activity depth
        total_weeks = min(total_weeks, max_activity_weeks)

        # Clamp to allowed range
        total_weeks = max(MIN_WEEKS, min(MAX_WEEKS, total_weeks))

        # Apply min/max thresholds
        total_weeks = max(MIN_WEEKS, min(MAX_WEEKS, total_weeks))

        topics_output = []
        for topic in curriculum.topics:
            activities = self._generate_activities(topic)
            week_distribution = self._distribute_activities(activities, total_weeks)

            topic_dict = {
                "name": topic.name,
                "description": topic.description,
                "project": topic.project,
                "dataset_metadata": getattr(topic, "dataset_metadata", None),
                "weeks": week_distribution,
            }
            topics_output.append(topic_dict)

        return {
            "subject": curriculum.subject,
            "grade": curriculum.grade,
            "weeks": total_weeks,
            "topics": topics_output,
        }

    # ---------------------------
    # Estimate total weeks dynamically
    # ---------------------------
    def _estimate_weeks(self, topics):
        """
        Heuristic: more classes/images -> more weeks.
        """
        total_weeks = 0
        for topic in topics:
            meta = getattr(topic, "dataset_metadata", None)
            if meta:
                num_classes = meta.get("num_classes", 2)
                total_images = meta.get("total_images", 1000)
                imbalance = meta.get("imbalance_ratio", 1)
                weeks = math.ceil((num_classes * 0.5 + total_images / 5000 + imbalance / 3))
            else:
                weeks = 2  # default minimal weeks if no dataset
            total_weeks = max(total_weeks, weeks)
        # Clamp within thresholds
        return max(MIN_WEEKS, min(MAX_WEEKS, total_weeks))

    # ---------------------------
    # Generate activities for a topic
    # ---------------------------
    def _generate_activities(self, topic):
        activities = []

        # Week 1 – Context
        activities.append(f"Introduction to {topic.name} and its agricultural impact.")

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
        # activities.append("Reflection, limitations, and ethical AI discussion.")

        return activities

    # ---------------------------
    # Split activities across weeks
    # ---------------------------
    def _distribute_activities(self, activities, total_weeks):
        week_distribution = {f"Week {i}": [] for i in range(1, total_weeks + 1)}

        # Distribute instructional activities evenly
        for idx, activity in enumerate(activities):
            week_number = (idx % total_weeks) + 1
            week_distribution[f"Week {week_number}"].append(activity)

        # Ensure reflection is always last week
        week_distribution[f"Week {total_weeks}"].append(
            "Reflection, limitations, and ethical AI discussion."
        )

        return week_distribution