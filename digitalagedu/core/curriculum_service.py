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
        if not self.dynamic_weeks and curriculum.weeks is not None:
            total_weeks = curriculum.weeks
        else:
            total_weeks = self._estimate_weeks(curriculum.topics)

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
        activities = [
            f"Discuss the importance of {topic.name}.",
        ]
        if hasattr(topic, "dataset_metadata") and topic.dataset_metadata:
            meta = topic.dataset_metadata
            classes = meta.get("num_classes", 0)
            images = meta.get("total_images", 0)
            imbalance = meta.get("imbalance_ratio", 0)
            activities.extend([
                f"Analyze dataset with {classes} classes and {images} images.",
                "Study techniques for handling class imbalance." if imbalance > 1 else "Explore dataset characteristics.",
                "Train classification model and analyze confusion matrix.",
            ])
        activities.append("Reflection and Q&A session.")
        return activities

    # ---------------------------
    # Split activities across weeks
    # ---------------------------
    def _distribute_activities(self, activities, total_weeks):
        week_distribution = {}
        num_activities = len(activities)
        activities_per_week = max(1, math.ceil(num_activities / total_weeks))

        for week in range(1, total_weeks + 1):
            start_idx = (week - 1) * activities_per_week
            end_idx = start_idx + activities_per_week
            week_activities = activities[start_idx:end_idx]
            if week_activities:
                week_distribution[f"Week {week}"] = week_activities

        return week_distribution