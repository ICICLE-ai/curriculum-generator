"""
Pydantic v2 schemas for Phase 2 LLM Curriculum Generation.
"""

from digitalagedu.core.llm.schemas.module_types import (
    Module,
    SyllabusModuleSchema,
    SyllabusPlanSchema,
)
from digitalagedu.core.llm.schemas.generation_types import (
    ProblemStatementSchema,
    Slide,
    SlideDeckSchema,
    ExerciseSolutionSchema,
    UnitTestSchema,
    ValidatedExerciseSchema,
)

__all__ = [
    "Module",
    "SyllabusModuleSchema",
    "SyllabusPlanSchema",
    "ProblemStatementSchema",
    "Slide",
    "SlideDeckSchema",
    "ExerciseSolutionSchema",
    "UnitTestSchema",
    "ValidatedExerciseSchema",
]
