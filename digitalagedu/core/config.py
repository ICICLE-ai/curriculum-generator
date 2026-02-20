from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import BaseModel, Field

# --- Pydantic models for validation --- #

class Topic(BaseModel):
    name: str
    description: str
    project: str
    dataset_path: Optional[str] = None

class CurriculumConfig(BaseModel):
    subject: str
    grade: int
    weeks: int = Field(..., gt=0, description="Number of weeks in the curriculum")
    topics: List[Topic]

class RootConfig(BaseModel):
    curriculum: CurriculumConfig

# --- Loader function --- #

def load_config(config_path: str) -> RootConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    config = RootConfig(**data)
    return config
