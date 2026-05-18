from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any

from digitalagedu.core.dataset_registry import DATASET_REGISTRY

# -----------------------------------------------------
# Topic Model
# -----------------------------------------------------
class Topic(BaseModel):
    name: str
    description: str
    project: str
    dataset_id: Optional[str] = None  # Controlled dataset selection
    dataset_metadata: Optional[Dict[str, Any]] = None

    @validator("dataset_id")
    def validate_dataset_id(cls, value):
        if value is not None and value not in DATASET_REGISTRY:
            raise ValueError(
                f"Invalid dataset_id '{value}'. "
                f"Allowed values: {list(DATASET_REGISTRY.keys())}"
            )
        return value

# -----------------------------------------------------
# Models Making up The Root Model
# -----------------------------------------------------
class ProjectModel(BaseModel):
    domain: str
    context_statement: str
    use_case: str

class DatasetModel(BaseModel):
    root_path: str
    structure: str
    train_split: float
    validation_split: float
    ignore_list: List[str]
    save_class_mapping: bool

class OutputModel(BaseModel):
    directory: str
    save_plots: bool
    artifact_path: str

class ExecutionModel(BaseModel):
    environment: str
    device: str
    batch_size: int
    image_size: int

class PipelineStageModel(BaseModel):
    name: str
    active: bool
    task_type: str
    module: str
    model_path: Optional[str] = None
    prompt: Optional[str] = None
    target_metric: Optional[str] = None

class PipelineModel(BaseModel):
    stages: List[PipelineStageModel]

class ResourceModel(BaseModel):
    name: str
    url: str


# -----------------------------------------------------
# Curriculum Model
# -----------------------------------------------------
class CurriculumConfig(BaseModel):
    subject: str
    grade: int
    weeks: Optional[int] = Field(
        None, description="Optional number of weeks; if not provided, calculated dynamically"
    )
    topics: List[Topic]
    resources: Optional[List[ResourceModel]] = None

    @validator("weeks")
    def check_weeks_range(cls, value):
        if value is not None:
            if value < 4 or value > 16:
                raise ValueError("Curriculum weeks must be between 4 and 16")
        return value

# -----------------------------------------------------
# Root Model
# -----------------------------------------------------
class RootConfig(BaseModel):
    project: ProjectModel
    dataset: DatasetModel
    output: OutputModel
    pipeline: PipelineModel
    execution: ExecutionModel
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