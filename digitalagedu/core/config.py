from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field, validator

from digitalagedu.core.dataset_registry import DATASET_REGISTRY


# -----------------------------------------------------
# Topic Model
# -----------------------------------------------------
class Topic(BaseModel):
    name: str
    description: str
    project: str
    dataset_id: Optional[str] = None  # Controlled dataset selection

    @validator("dataset_id")
    def validate_dataset_id(cls, value):
        if value is not None and value not in DATASET_REGISTRY:
            raise ValueError(
                f"Invalid dataset_id '{value}'. "
                f"Allowed values: {list(DATASET_REGISTRY.keys())}"
            )
        return value


# -----------------------------------------------------
# Curriculum Model
# -----------------------------------------------------
class CurriculumConfig(BaseModel):
    subject: str
    grade: int
    weeks: int = Field(..., gt=0, description="Number of weeks in the curriculum")
    topics: List[Topic]


# -----------------------------------------------------
# Root Model
# -----------------------------------------------------
class RootConfig(BaseModel):
    curriculum: CurriculumConfig


# -----------------------------------------------------
# Loader Function
# -----------------------------------------------------
def load_config(config_path: str) -> RootConfig:
    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    config = RootConfig(**data)
    return config