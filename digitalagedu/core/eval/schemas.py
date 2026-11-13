"""Structured replies of the evaluation models. Evidence fields come before scores, so the model reasons first."""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

BLOOM_LEVELS = ["remember", "understand", "apply", "analyze", "evaluate", "create"]
BloomLevel = Literal["remember", "understand", "apply", "analyze", "evaluate", "create"]


class RubricScore(BaseModel):
    dimension: str = Field(description="The rubric dimension id, exactly as listed")
    evidence: str = Field(description="Quotes or specific observations from the materials that justify the score")
    score: int = Field(ge=1, le=5, description="1 (worst) to 5 (best), per the dimension's anchors")


class RubricVerdict(BaseModel):
    scores: List[RubricScore] = Field(description="One entry per rubric dimension")


class BloomObjective(BaseModel):
    objective: str = Field(description="The learning objective, verbatim")
    rationale: str = Field(description="Which verb and task in the objective set its cognitive level")
    level: BloomLevel = Field(description="Bloom's revised taxonomy level")


class BloomLevels(BaseModel):
    objectives: List[BloomObjective]


class TestMapping(BaseModel):
    test_name: str = Field(description="The test function name (or 'module' for top-level asserts)")
    quoted_assert: str = Field(description="The assert line(s) that show what the test checks, verbatim")
    checks_only_structure: bool = Field(
        description="True if the test only checks shapes, types, keys or that code runs, not computed values or behavior")
    objective_index: Optional[int] = Field(
        description="0-based index of the objective this test assesses, or null if it assesses none")


class TestMap(BaseModel):
    tests: List[TestMapping]


class QuizQuestion(BaseModel):
    question: str
    options: List[str] = Field(min_length=4, max_length=4)
    answer_index: int = Field(ge=0, le=3)
    kind: Literal["run_data", "concept"] = Field(
        description="run_data: answerable only from this run's results; concept: general understanding")
    objective_index: int = Field(ge=0, description="0-based index of the objective this question assesses")


class Quiz(BaseModel):
    questions: List[QuizQuestion] = Field(min_length=6, max_length=14)


class QuizAnswers(BaseModel):
    answers: List[int] = Field(description="One chosen option index (0-3) per question, in order")
