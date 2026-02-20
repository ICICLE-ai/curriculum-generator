"""
Dataset metadata schema inspired by dataset card principles.

This structured representation transforms raw filesystem datasets
into pedagogically actionable metadata.
"""

from typing import Dict, List
from pydantic import BaseModel, Field


class DatasetMetadata(BaseModel):
    # Basic structural info
    dataset_path: str = Field(..., description="Filesystem path to dataset")
    num_classes: int = Field(..., description="Number of classification labels")
    total_images: int = Field(..., description="Total number of images")
    images_per_class: Dict[str, int] = Field(
        ..., description="Mapping of class names to image counts"
    )

    # Statistical properties
    imbalance_ratio: float = Field(
        ..., description="Ratio between largest and smallest class"
    )
    size_category: str = Field(
        ..., description="Dataset size category (small/medium/large)"
    )

    # Educational inference
    task_type: str = Field(
        ..., description="Type of ML task inferred from structure"
    )
    difficulty_level: str = Field(
        ..., description="Suggested difficulty level for curriculum"
    )
    suggested_metrics: List[str] = Field(
        ..., description="Evaluation metrics recommended for this dataset"
    )

    def summary(self) -> str:
        """
        Returns a readable summary of dataset metadata.
        """
        return (
            f"Dataset at {self.dataset_path}\n"
            f"Classes: {self.num_classes}\n"
            f"Total Images: {self.total_images}\n"
            f"Imbalance Ratio: {self.imbalance_ratio:.2f}\n"
            f"Size Category: {self.size_category}\n"
            f"Difficulty Level: {self.difficulty_level}"
        )
