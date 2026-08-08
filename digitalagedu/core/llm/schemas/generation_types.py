from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from digitalagedu.core.llm.sandbox import run_in_sandbox

class ProblemStatementSchema(BaseModel):
    """Schema for Agent 0: Curriculum Director / Problem Formulation Agent"""
    title: str = Field(description="Domain-grounded title of the coding exercise")
    domain_context: str = Field(description="Summary of Phase 1 dataset, task, and class labels derived dynamically from telemetry")
    problem_statement: str = Field(description="Detailed exercise directive focusing on Phase 1 failure modes (e.g. high false negative/positive rates, low precision, segmentation or regression error)")
    learning_objectives: List[str] = Field(description="2-3 specific learning outcomes based on Bloom's taxonomy")
    target_input_shape: str = Field(description="Tensor shape contract for synthetic input (e.g. [batch_size, channels, ...] or [batch_size, seq_len, features])")
    target_output_shape: str = Field(description="Tensor shape contract for model output (e.g. [batch_size, num_classes] or [batch_size, 1, H, W])")
    suggested_focus: str = Field(description="Core technical implementation focus (e.g. Weighted Loss, Feature Attribution Hooks, Custom Layers, Data Augmentation)")
    markdown_overview: str = Field(description="Comprehensive Markdown document (.md) explaining: (1) The core PyTorch/Deep Learning concept, (2) How it directly relates to the Phase 1 dataset telemetry & failure modes, and (3) What the student is trying to solve in the hands-on exercise.")

class Slide(BaseModel):
    title: str = Field(description="Title of the slide")
    bullet_points: List[str] = Field(description="3 to 4 concise bullet points explaining key concepts")
    code_snippet: Optional[str] = Field(None, description="Optional PyTorch snippet for code demonstration")

class SlideDeckSchema(BaseModel):
    deck_title: str = Field(description="Main topic or title of presentation")
    slides: List[Slide] = Field(description="List of presentation slides")

class ExerciseSolutionSchema(BaseModel):
    """Schema for Stage 1: Generator Agent (Curriculum Code Educator)"""
    title: str = Field(description="Title of the coding exercise")
    instructions: str = Field(description="Problem statement and student directives")
    starter_code: str = Field(description="Starter PyTorch skeleton code containing TODO comments")
    solution_code: str = Field(description="Complete PyTorch reference solution code starting with required imports")

class UnitTestSchema(BaseModel):
    """Schema for Stage 2: QA Agent (Software Test Engineer)"""
    unit_test: str = Field(description="Standalone PyTorch unit test code containing assertions to verify the reference solution")

class ValidatedExerciseSchema(BaseModel):
    """Integrated Exercise Schema holding validated solution and unit tests"""
    title: str = Field(description="Title of the coding exercise")
    instructions: str = Field(description="Problem statement and student directives")
    starter_code: str = Field(description="Starter PyTorch skeleton code containing TODO comments")
    solution_code: str = Field(description="Complete PyTorch reference solution code. Must start with required imports.")
    unit_test: str = Field(description="Standalone PyTorch unit tests with assertions to verify solution_code.")

    @model_validator(mode="after")
    def validate_solution_with_unit_tests(self):
        """Runs solution code against unit test in a sandbox with hybrid diagnostic feedback"""
        success, log = run_in_sandbox(self.solution_code, self.unit_test)
        if not success:
            raise ValueError(
                f"Generated solution failed unit test verification in sandbox.\n"
                f"{log}\n"
                f"Please fix the implementation errors in solution_code or unit_test."
            )
        return self
