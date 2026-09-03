"""
Pydantic v2 schemas for Phase 2 LLM Curriculum Generation.
"""

from digitalagedu.core.llm.schemas.module_types import (
    Module,
    SyllabusModuleSchema,
    SyllabusPlanSchema,
)
from digitalagedu.core.llm.schemas.generation_types import (
    ComponentSpec,
    MilestoneSubsystem,
    ProblemStatementSchema,
    Slide,
    SlideDeckSchema,
    ExerciseSolutionSchema,
    StarterCodeSchema,
    UnitTestSchema,
    ValidatedExerciseSchema,
)

__all__ = [
    "Module",
    "SyllabusModuleSchema",
    "SyllabusPlanSchema",
    "ComponentSpec",
    "MilestoneSubsystem",
    "ProblemStatementSchema",
    "Slide",
    "SlideDeckSchema",
    "ExerciseSolutionSchema",
    "StarterCodeSchema",
    "UnitTestSchema",
    "ValidatedExerciseSchema",
]
