from digitalagedu.core.dataset_registry import DATASET_REGISTRY
from digitalagedu.core.dataset_scanner import DatasetScanner


class CurriculumService:
    def __init__(self, config):
        self.config = config

    def build(self):
        curriculum = self.config.curriculum

        structured_topics = []

        for topic in curriculum.topics:

            dataset_metadata = None

            if getattr(topic, "dataset_id", None):
                if topic.dataset_id not in DATASET_REGISTRY:
                    raise ValueError(f"Invalid dataset_id: {topic.dataset_id}")

                dataset_info = DATASET_REGISTRY[topic.dataset_id]

                scanner = DatasetScanner(
                    dataset_path=dataset_info["path"],
                    allowed_subfolders=dataset_info.get("allowed_subfolders"),
                    task_type=dataset_info.get("task_type", "image-classification"),
                )

                dataset_metadata = scanner.scan()

            structured_topics.append(
                {
                    "name": topic.name,
                    "description": topic.description,
                    "project": topic.project,
                    "dataset_metadata": dataset_metadata,
                    "activities": self._generate_activities(
                        topic.name,
                        dataset_metadata,
                    ),
                }
            )

        return {
            "subject": curriculum.subject,
            "grade": curriculum.grade,
            "weeks": curriculum.weeks,
            "topics": structured_topics,
        }

    # -----------------------------------------------------
    # Activity Generator (Now Dataset-Aware)
    # -----------------------------------------------------
    def _generate_activities(self, topic_name: str, metadata):

        activities = [
            f"Discuss the importance of {topic_name}.",
        ]

        if metadata:
            activities.append(
                f"Analyze dataset with {metadata.num_classes} classes and {metadata.total_images} images."
            )

            if metadata.imbalance_ratio > 3:
                activities.append(
                    "Study techniques for handling class imbalance."
                )

            if metadata.task_type == "segmentation":
                activities.append(
                    "Implement segmentation model and evaluate using IoU."
                )

            elif metadata.task_type == "measurement":
                activities.append(
                    "Perform quantitative size estimation and evaluate using MAE."
                )

            else:
                activities.append(
                    "Train classification model and analyze confusion matrix."
                )

        activities.append("Reflection and Q&A session.")

        return activities