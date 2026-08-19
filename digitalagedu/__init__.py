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
    "TemplateRenderer",
    "FileWriter",
    "generate_llm_curriculum",
]

def generate_llm_curriculum(*args, **kwargs):
    from digitalagedu.core.llm.main import generate_llm_curriculum as _gen
    return _gen(*args, **kwargs)

