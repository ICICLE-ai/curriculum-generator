from pathlib import Path
from typing import List, Dict, Union

from .dataset_metadata import DatasetMetadata
from .dataset_exceptions import DatasetValidationError, UnsupportedDatasetStructureError


class DatasetScanner:
    VALID_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}
    IGNORED_FOLDERS = {"__pycache__"}

    SIZE_CATEGORIES = [
        ("n<1K", 0, 1000),
        ("1K<n<10K", 1000, 10000),
        ("10K<n<100K", 10000, 100000),
        ("100K<n<1M", 100000, 1000000),
        ("n>1M", 1000000, float("inf")),
    ]

    def __init__(self, dataset_input: Union[Dict, str]):
        """
        Supports:
        1) Registry entry dict
        2) Direct dataset path string
        """
        if isinstance(dataset_input, dict):
            self.base_path = Path(dataset_input["path"])
            self.task_type = dataset_input.get("task_type", "classification")
            self.allowed_subfolders = dataset_input.get("allowed_subfolders")
        elif isinstance(dataset_input, str):
            self.base_path = Path(dataset_input)
            self.task_type = "classification"
            self.allowed_subfolders = None
        else:
            raise TypeError("DatasetScanner expects dict (registry entry) or str (path).")

        self.metadata: DatasetMetadata | None = None

    # -----------------------------------------------------
    # Validate Dataset Structure
    # -----------------------------------------------------
    def validate_structure(self) -> List[Path]:
        if not self.base_path.exists():
            raise DatasetValidationError(f"Dataset path does not exist: {self.base_path}")
        if not self.base_path.is_dir():
            raise DatasetValidationError(f"Provided path is not a directory: {self.base_path}")

        class_dirs: List[Path] = []

        if self.allowed_subfolders:
            for subfolder in self.allowed_subfolders:
                folder_path = self.base_path / subfolder
                if folder_path.exists():
                    class_dirs.extend(self._collect_class_dirs(folder_path))
        else:
            # If no allowed_subfolders, scan all first-level directories
            for sub in self.base_path.iterdir():
                if sub.is_dir() and sub.name not in self.IGNORED_FOLDERS:
                    class_dirs.extend(self._collect_class_dirs(sub))

        if len(class_dirs) < 1:
            raise UnsupportedDatasetStructureError(
                f"No valid class subdirectories found in {self.base_path}"
            )

        return class_dirs

    # -----------------------------------------------------
    # Collect class directories recursively (one level deeper)
    # -----------------------------------------------------
    def _collect_class_dirs(self, folder: Path) -> List[Path]:
        class_dirs: List[Path] = []

        # Check if folder has images directly
        if any(f.suffix.lower() in self.VALID_IMAGE_EXTENSIONS for f in folder.rglob("*") if f.is_file()):
            class_dirs.append(folder)
        else:
            # Look one level deeper for class folders
            for sub in folder.iterdir():
                if sub.is_dir() and sub.name not in self.IGNORED_FOLDERS:
                    class_dirs.append(sub)

        return class_dirs

    # -----------------------------------------------------
    # Extract Class Info
    # -----------------------------------------------------
    def extract_class_info(self, class_dirs: List[Path]) -> Dict[str, int]:
        images_per_class = {}

        for class_dir in class_dirs:
            image_count = sum(
                1 for file in class_dir.rglob("*")
                if file.is_file() and file.suffix.lower() in self.VALID_IMAGE_EXTENSIONS
                and all(part not in self.IGNORED_FOLDERS for part in file.parts)
            )

            if image_count == 0:
                # Skip empty folders instead of raising error
                continue

            images_per_class[class_dir.name] = image_count

        if len(images_per_class) == 0:
            raise DatasetValidationError(
                f"No valid image files found in any class folder under: {self.base_path}"
            )

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
    # Educational Metadata
    # -----------------------------------------------------
    def infer_educational_metadata(
        self,
        total_images: int,
        num_classes: int,
        imbalance_ratio: float,
    ):
        if self.task_type in ["segmentation", "measurement"]:
            return "advanced", ["IoU", "Dice Score", "MAE"]

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
    # Scan
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
            dataset_path=str(self.base_path),
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