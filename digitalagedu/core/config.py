from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field, validator, model_validator
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
    use_case: Optional[str] = None

class DatasetModel(BaseModel):
    root_path: str
    structure: Optional[str] = None
    train_split: Optional[float] = None
    validation_split: Optional[float] = None
    ignore_list: Optional[List[str]] = None
    save_class_mapping: Optional[bool] = True

class OutputModel(BaseModel):
    directory: str
    save_plots: Optional[bool] = None
    artifact_path: Optional[str] = None

class ExecutionModel(BaseModel):
    environment: Optional[str] = None
    device: str
    batch_size: int
    image_size: int
    max_samples: Optional[int] = None
    seed: Optional[int] = None

class PipelineStageModel(BaseModel):
    name: str
    active: bool
    task_type: str
    module: Optional[str] = None
    model_path: Optional[str] = None
    prompt: Optional[str] = None
    target_metric: Optional[str] = None

class PipelineModel(BaseModel):
    stages: List[PipelineStageModel]

class ResourceModel(BaseModel):
    name: str
    url: str

# -----------------------------------------------------
# Curriculum Module Model
# -----------------------------------------------------
class CurriculumModuleModel(BaseModel):
    id: str
    weeks: int = Field(1, ge=1,le=4,description="Duration in weeks for this module.")



# -----------------------------------------------------
# Curriculum Model
# -----------------------------------------------------
class CurriculumConfig(BaseModel):
    subject: str
    grade: int
    weeks: Optional[int] = Field(
        None, description="Optional number of weeks; if not provided, calculated dynamically if modules provided"
    )

    modules: Optional[List[CurriculumModuleModel]] = None
    topics: List[Topic]
    resources: Optional[List[ResourceModel]] = None

    @validator("weeks")
    def check_weeks_range(cls, value):
        if value is not None:
            if value < 4 or value > 24:
                raise ValueError("Curriculum weeks must be between 4 and 24")
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

    @model_validator(mode='after')
    def resolve_implicit_pipeline_defaults(self):
        project = self.project
        pipeline = self.pipeline

        if project and pipeline:
            use_case_clean = project.use_case.lower().replace(" ", "_")
            for stage in pipeline.stages:
                # 1. Resolve missing Modules based on stage name
                if not stage.module:
                    if stage.name == "Classification":
                        stage.module = "curriculum_resources.week_08.solution"
                    elif stage.name == "Segmentation":
                        stage.module = "curriculum_resources.week_09.solution"
                    elif stage.name in ["VisionQA", "VisualXAI"]:
                        stage.module = "curriculum_resources.xai.solution"

                # 2. Resolve missing Model Paths dynamically
                if not stage.model_path:
                    if stage.name in ["Classification", "VisualXAI"]:
                        stage.model_path = f"models/dinov2_{use_case_clean}_classifier.pth"
                    elif stage.name == "Segmentation":
                        stage.model_path = "models/sam_vit_b.pth"
        return self

    

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