from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from digitalagedu.core.llm.sandbox import run_in_sandbox

class ComponentSpec(BaseModel):
    """Specification of an individual class, function, or data structure within a subsystem"""
    name: str = Field(description="Name of the function, class, or data structure (e.g. 'validate_batch', 'DataBatchConfig', 'ClassifierModel')")
    kind: str = Field(description="Type of symbol: 'function' | 'class' | 'dataclass'")
    signature: str = Field(description="Complete Python signature with type hints (e.g. 'def validate_batch(samples: list) -> bool:')")
    description: str = Field(description="Concise description of the component's role and responsibility")

class MilestoneSubsystem(BaseModel):
    """A substantive engineering subsystem within the mini-project, containing cooperating components"""
    milestone_num: int = Field(description="Milestone number (1, 2, or 3)")
    title: str = Field(description="Descriptive title of the subsystem")
    objective: str = Field(description="Specific learning outcome addressed by this subsystem")
    components: List[ComponentSpec] = Field(description="Cluster of cooperating classes, functions, or data structures that form this subsystem")

class ProblemStatementSchema(BaseModel):
    """Schema for Agent 0: Curriculum Director / Problem Formulation Agent"""
    title: str = Field(description="Domain-grounded title of the coding exercise")
    domain_context: str = Field(description="Summary of Phase 1 dataset, task, and class labels derived dynamically from telemetry")
    problem_statement: str = Field(description="Detailed exercise directive focusing on domain challenge and Phase 1 failure modes")
    learning_objectives: List[str] = Field(description="2-3 specific learning outcomes based on Bloom's taxonomy")
    milestone_subsystems: List[MilestoneSubsystem] = Field(
        default_factory=list,
        description="3 substantive milestone subsystems, each containing multiple cooperating classes and functions"
    )
    pipeline_orchestrator_signature: str = Field(
        default="def run_pipeline() -> dict:",
        description="Signature of the overarching pipeline orchestrator function connecting all 3 subsystems"
    )
    target_input_shape: Optional[str] = Field(None, description="Optional input contract or data dimensions")
    target_output_shape: Optional[str] = Field(None, description="Optional output contract or return format")
    suggested_focus: str = Field(description="Core technical implementation focus")
    source_artifacts: List[str] = Field(
        default_factory=list,
        description="Stable artifact IDs from the workflow provenance manifest that ground this module (e.g. ['artifact_run_42_parallel_telemetry'])"
    )
    markdown_overview: str = Field(description="Comprehensive Markdown document (.md) explaining concepts, telemetry connections, and student objectives")

class Slide(BaseModel):
    title: str = Field(description="Title of the slide")
    bullet_points: List[str] = Field(description="3 to 4 concise bullet points explaining key concepts")
    code_snippet: Optional[str] = Field(None, description="Optional code demonstration snippet")

class SlideDeckSchema(BaseModel):
    deck_title: str = Field(description="Main topic or title of presentation")
    slides: List[Slide] = Field(description="List of presentation slides")

class ExerciseSolutionSchema(BaseModel):
    """Schema for Stage 1: Generator Agent (Curriculum Code Educator)"""
    title: str = Field(description="Title of the coding exercise")
    instructions: str = Field(description="Problem statement and student directives")
    starter_code: Optional[str] = Field(None, description="Starter Python skeleton code containing TODO comments")
    solution_code: str = Field(description="Complete, robust Python reference solution (150-250 lines) starting with all required imports and implementing all milestone subsystems and run_pipeline()")

class StarterCodeSchema(BaseModel):
    """Schema for scaffolding verified solution into student starter code"""
    starter_code: str = Field(description="Scaffolded Python starter code with guided # Step 1, # Step 2 TODO directives derived from the verified solution")

class UnitTestSchema(BaseModel):
    """Schema for Stage 2: QA Agent (Software Test Engineer)"""
    unit_test: str = Field(description="Standalone Python unit test code asserting each component within the milestone subsystems and the overarching pipeline")

class ValidatedExerciseSchema(BaseModel):
    """Integrated Exercise Schema holding validated solution and unit tests"""
    title: str = Field(description="Title of the coding exercise")
    instructions: str = Field(description="Problem statement and student directives")
    starter_code: str = Field(description="Starter Python skeleton code containing TODO comments")
    solution_code: str = Field(description="Complete Python reference solution code. Must start with required imports.")
    unit_test: str = Field(description="Standalone Python unit tests with assertions to verify solution_code.")

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


class ModuleManifestSchema(BaseModel):
    """
    Formal Pydantic contract for [module_id]_manifest.json enforcing
    all Table 1 provenance and governance fields. Missing or empty required
    fields trigger a ValidationError rather than serializing incomplete null data.
    """
    module_id: str = Field(..., min_length=1, description="Unique identifier for the curriculum module")
    title: str = Field(..., min_length=1, description="Human-readable module title")
    academic_week: int = Field(..., ge=1, description="Target curriculum week (>= 1)")
    difficulty: str = Field(..., min_length=1, description="Pedagogical difficulty level")
    workflow_run_id: str = Field(..., min_length=1, description="Identifies the source execution run")
    dataset_version: str = Field(..., min_length=1, description="Identifies the dataset context")
    model_version: str = Field(..., min_length=1, description="Identifies the model context")
    configuration_hash: str = Field(..., min_length=1, description="Cryptographic SHA-256 hash of workflow configuration")
    source_artifacts: List[str] = Field(..., min_length=1, description="List of validated artifact IDs linked to this module")
    learning_objective_tags: List[str] = Field(..., min_length=1, description="Pedagogical objective tags")
    learner_role: str = Field(..., min_length=1, description="Target learner role (e.g., student_practitioner)")
    permitted_representation: str = Field(..., min_length=1, description="Permitted representation format")
    selection_rule: str = Field(..., min_length=1, description="Pedagogical artifact selection rule")
    validation_status: str = Field(default="VERIFIED", pattern="^(VERIFIED|FAILED)$", description="Workflow validation status")

