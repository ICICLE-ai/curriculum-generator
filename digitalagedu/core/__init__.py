"""
DigitalAgEdu Core Engine Package
================================
Provides Pydantic configuration schemas, curriculum orchestration,
dataset scanning, execution metrics, and automated exercise synthesis.
"""

from digitalagedu.core.config import (
    load_config,
    RootConfig,
    ProjectModel,
    DatasetModel,
    OutputModel,
    ExecutionModel,
    PipelineStageModel,
    PipelineModel,
    ResourceModel,
    CurriculumModuleModel,
    CurriculumConfig,
    Topic,
)
from digitalagedu.core.curriculum_service import CurriculumService
from digitalagedu.core.dataset_scanner import DatasetScanner
from digitalagedu.core.dataset_metadata import DatasetMetadata
from digitalagedu.core.learning_outcomes_service import LearningOutcomesService
from digitalagedu.core.metrics import generate_run_report
from digitalagedu.core.orchestrator import CurriculumEngine
from digitalagedu.core.renderer import TemplateRenderer
from digitalagedu.core.writer import FileWriter

__all__ = [
    "load_config",
    "RootConfig",
    "ProjectModel",
    "DatasetModel",
    "OutputModel",
    "ExecutionModel",
    "PipelineStageModel",
    "PipelineModel",
    "ResourceModel",
    "CurriculumModuleModel",
    "CurriculumConfig",
    "Topic",
    "CurriculumService",
    "DatasetScanner",
    "DatasetMetadata",
    "LearningOutcomesService",
    "generate_run_report",
    "CurriculumEngine",
    "TemplateRenderer",
    "FileWriter",
    "generate_llm_curriculum",
]

def generate_llm_curriculum(*args, **kwargs):
    from digitalagedu.core.llm.main import generate_llm_curriculum as _gen
    return _gen(*args, **kwargs)

