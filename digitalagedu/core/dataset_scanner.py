"""
Dataset scanner for DigitalAgEdu.

Now supports:
- Controlled dataset registry
- Optional subfolder restriction
- Task type override (classification, segmentation, measurement)
"""

from pathlib import Path
from typing import List, Dict, Optional

from .dataset_metadata import DatasetMetadata
from .dataset_exceptions import (
    DatasetValidationError,
    UnsupportedDatasetStructureError,
)


class DatasetScanner:

    VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

    SIZE_CATEGORIES = [
        ("n<1K", 0, 1000),
        ("1K<n<10K", 1000, 10000),
        ("10K<n<100K", 10000, 100000),
        ("100K<n<1M", 100000, 1000000),
        ("n>1M", 1000000, float("inf")),
    ]

    IGNORED_FOLDERS = {"soybean_final_dataset", "__pycache__"}

    def __init__(
        self,
        dataset_path: str,
        allowed_subfolders: Optional[List[str]] = None,
        task_type: str = "image-classification",
    ):
        self.dataset_path = Path(dataset_path)
        self.allowed_subfolders = allowed_subfolders
        self.task_type = task_type
        self.metadata: DatasetMetadata | None = None

    # -----------------------------------------------------
    # Structure Validation
    # -----------------------------------------------------
    def validate_structure(self) -> List[Path]:

        if not self.dataset_path.exists():
            raise DatasetValidationError(
                f"Dataset path does not exist: {self.dataset_path}"
            )

        if not self.dataset_path.is_dir():
            raise DatasetValidationError(
                f"Provided path is not a directory: {self.dataset_path}"
            )

        # If allowed_subfolders provided → restrict strictly
        if self.allowed_subfolders:
            class_dirs = [
                self.dataset_path / folder
                for folder in self.allowed_subfolders
                if (self.dataset_path / folder).is_dir()
            ]
        else:
            class_dirs = [
                d for d in self.dataset_path.iterdir()
                if d.is_dir() and d.name not in self.IGNORED_FOLDERS
            ]

        if len(class_dirs) < 2:
            raise UnsupportedDatasetStructureError(
                "Dataset must contain at least two valid class subdirectories."
            )

        return class_dirs

    # -----------------------------------------------------
    # Extract Class Structure (Recursive)
    # -----------------------------------------------------
    def extract_class_info(self, class_dirs: List[Path]) -> Dict[str, int]:

        images_per_class = {}

        for class_dir in class_dirs:
            image_count = 0

            for file in class_dir.rglob("*"):
                if any(part in self.IGNORED_FOLDERS for part in file.parts):
                    continue

                if file.is_file() and file.suffix.lower() in self.VALID_IMAGE_EXTENSIONS:
                    image_count += 1

            if image_count == 0:
                raise DatasetValidationError(
                    f"No valid image files found in class folder: {class_dir.name}"
                )

            images_per_class[class_dir.name] = image_count

        return images_per_class

    # -----------------------------------------------------
    # Compute Statistics
    # -----------------------------------------------------
    def compute_statistics(self, images_per_class: Dict[str, int]):
        total_images = sum(images_per_class.values())
        num_classes = len(images_per_class)

        max_count = max(images_per_class.values())
        min_count = min(images_per_class.values())

        imbalance_ratio = max_count / min_count if min_count > 0 else 0

        size_category = "Unknown"

        for label, min_val, max_val in self.SIZE_CATEGORIES:
            if min_val < total_images <= max_val:
                size_category = label
                break

        return total_images, num_classes, imbalance_ratio, size_category

    # -----------------------------------------------------
    # Educational Metadata Inference
    # -----------------------------------------------------
    def infer_educational_metadata(
        self,
        total_images: int,
        num_classes: int,
        imbalance_ratio: float,
    ):

        if self.task_type in ["segmentation", "measurement"]:
            difficulty = "advanced"
            metrics = ["IoU", "Dice Score", "MAE"]
            return difficulty, metrics

        # Default: classification logic
        if num_classes == 2 and total_images < 1000:
            difficulty = "beginner"
        elif 3 <= num_classes <= 5 and total_images < 10000:
            difficulty = "intermediate"
        else:
            difficulty = "advanced"

        if num_classes == 2:
            metrics = ["Accuracy", "Precision", "Recall", "F1-score"]
        else:
            metrics = ["Accuracy", "Macro F1-score", "Confusion Matrix"]

        if imbalance_ratio > 3:
            metrics.append("Weighted F1-score")

        return difficulty, metrics

    # -----------------------------------------------------
    # Public Scan Method
    # -----------------------------------------------------
    def scan(self) -> DatasetMetadata:

        class_dirs = self.validate_structure()
        images_per_class = self.extract_class_info(class_dirs)

        total_images, num_classes, imbalance_ratio, size_category = (
            self.compute_statistics(images_per_class)
        )

        difficulty, metrics = self.infer_educational_metadata(
            total_images,
            num_classes,
            imbalance_ratio,
        )

        self.metadata = DatasetMetadata(
            dataset_path=str(self.dataset_path),
            num_classes=num_classes,
            total_images=total_images,
            images_per_class=images_per_class,
            imbalance_ratio=round(imbalance_ratio, 2),
            size_category=size_category,
            task_type=self.task_type,
            difficulty_level=difficulty,
            suggested_metrics=metrics,
        )

        return self.metadata