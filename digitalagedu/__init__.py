"""
DigitalAgEdu: An AI-driven educational framework integrating automated curriculum
generation with end-to-end computer vision pipelines.
"""

__version__ = "0.1.0"

from digitalagedu.core import (
    load_config,
    RootConfig,
    CurriculumConfig,
    Topic,
    CurriculumEngine,
    CurriculumService,
    DatasetScanner,
    PracticeGenerator,
    TemplateRenderer,
    FileWriter,
)

__all__ = [
    "load_config",
    "RootConfig",
    "CurriculumConfig",
    "Topic",
    "CurriculumEngine",
    "CurriculumService",
    "DatasetScanner",
    "PracticeGenerator",
    "TemplateRenderer",
    "FileWriter",
]
