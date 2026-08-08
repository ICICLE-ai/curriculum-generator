from pathlib import Path
from typing import List, Optional, Dict, Any, Union
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

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

    @field_validator("dataset_id")
    @classmethod
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
    # --- W&B Setup ---
    use_wandb: Optional[bool] = False
    use_profiler: Optional[bool] = False
    wandb_project: Optional[str] = "digitalagedu"
    # --- Phase 2 LLM Setup ---
    use_llm: Optional[bool] = False
    llm_base_url: Optional[str] = "http://localhost:8000/v1"
    llm_model: Optional[str] = "Qwen/Qwen2.5-Coder-32B-Instruct-AWQ"

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
    week: Optional[int] = Field(None, ge=1, le=24, description="Target week number.")
    weeks: Optional[int] = Field(None, ge=1, le=24, description="Duration in weeks or week alias.")
    title: Optional[str] = None
    context: Optional[str] = None
    difficulty: Optional[str] = None



# -----------------------------------------------------
# Curriculum Model
# -----------------------------------------------------
class CurriculumConfig(BaseModel):
    subject: str
    grade: Optional[Union[int, str]] = Field(10, description="Target grade or academic level")
    target_level: Optional[str] = None
    model: Optional[str] = None  # LLM model specification
    weeks: Optional[int] = Field(
        None, description="Optional number of weeks; if not provided, calculated dynamically if modules provided"
    )

    modules: Optional[List[CurriculumModuleModel]] = None
    topics: List[Topic] = []  # Default to empty list for modules-only configs
    resources: Optional[List[ResourceModel]] = None

    @field_validator("weeks")
    @classmethod
    def check_weeks_range(cls, value):
        if value is not None:
            if value < 4 or value > 24:
                raise ValueError("Curriculum weeks must be between 4 and 24")
        return value

# -----------------------------------------------------
# Root Model
# -----------------------------------------------------
class RootConfig(BaseModel):
    project: Optional[ProjectModel] = Field(default_factory=lambda: ProjectModel(domain="General AI", context_statement="General AI Curriculum"))
    dataset: Optional[DatasetModel] = Field(default_factory=lambda: DatasetModel(root_path="."))
    output: Optional[OutputModel] = Field(default_factory=lambda: OutputModel(directory="./output"))
    pipeline: Optional[PipelineModel] = Field(default_factory=lambda: PipelineModel(stages=[]))
    execution: Optional[ExecutionModel] = Field(default_factory=lambda: ExecutionModel(device="cpu", batch_size=16, image_size=518))
    curriculum: CurriculumConfig

    @model_validator(mode='after')
    def resolve_implicit_pipeline_defaults(self):
        project = self.project
        pipeline = self.pipeline

        if project and pipeline and pipeline.stages:
            use_case_clean = project.use_case.lower().replace(" ", "_") if project.use_case else "general"
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