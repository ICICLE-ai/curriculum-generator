from types import SimpleNamespace

from digitalagedu.core.config import CurriculumConfig, CurriculumModuleModel, ProjectModel, ResourceModel, RootConfig, Topic
from digitalagedu.core.llm.context import build_exercise_prompt, build_qa_prompt, build_scaffold_prompt
from digitalagedu.core.llm.main import _build_modules
from digitalagedu.core.llm.presentation_prompts import build_lesson_plan_prompt
from digitalagedu.core.llm.schemas import Module, ProblemStatementSchema
from digitalagedu.core.llm.telemetry import formulate_problem_statement


def test_build_modules_populates_course_context(tmp_path):
    cfg = RootConfig(
        project=ProjectModel(
            domain="Agricultural Science",
            context_statement="spotting crop leaf diseases from farm photos",
        ),
        curriculum=CurriculumConfig(
            subject="Intro to AI in Agriculture",
            target_level="High School STEM (Grades 9-12)",
            modules=[
                CurriculumModuleModel(
                    id="python_basics",
                    title="Python Basics",
                    week=1,
                    estimated_days=2.5,
                    context="Count class images using lists and loops",
                    difficulty="beginner",
                    learning_outcomes=["Count images per folder"],
                )
            ],
            topics=[Topic(name="Plant Health", description="Leaf disease classification", project="Plant Health")],
            resources=[ResourceModel(name="PlantVillage", url="https://example.org/plantvillage")],
        ),
    )

    modules = _build_modules(cfg, {}, None, "deepseek-v4-flash", str(tmp_path))
    assert len(modules) == 1
    m = modules[0]
    assert m.domain == "Agricultural Science"
    assert m.course_context == "spotting crop leaf diseases from farm photos"
    assert m.subject == "Intro to AI in Agriculture"
    assert "Plant Health: Leaf disease classification" in m.topic_focus
    assert m.estimated_days == 2.5
    assert m.resources == [{"name": "PlantVillage", "url": "https://example.org/plantvillage"}]

    block = m.course_context_block()
    assert "Course Subject: Intro to AI in Agriculture" in block
    assert "Domain: Agricultural Science" in block
    assert "Course Goal: spotting crop leaf diseases from farm photos" in block
    assert "Core Topic Focus: Plant Health: Leaf disease classification" in block
    assert "Estimated Module Duration: 2.5 day(s)" in block
    assert "PlantVillage: https://example.org/plantvillage" in block


def test_empty_course_context_block_when_unset():
    m = Module(id="m", title="M", week=1, context="c", difficulty="Beginner")
    assert m.course_context_block() == ""


def test_prompts_include_course_context(monkeypatch):
    captured = {}

    class _FakeCompletions:
        def create(self, **kwargs):
            captured["messages"] = kwargs["messages"]
            return ProblemStatementSchema(
                title="T",
                domain_context="D",
                problem_statement="P",
                learning_objectives=["Obj 1"],
                suggested_focus="F",
                milestone_subsystems=[],
                pipeline_orchestrator_signature="def run_pipeline() -> dict:",
                markdown_overview="Overview",
                source_artifacts=[],
            )

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=_FakeCompletions()))
    monkeypatch.setattr("digitalagedu.core.llm.context.get_rag_context", lambda *a, **k: "")

    m = Module(
        id="m1",
        title="Python Basics",
        week=1,
        context="Count images",
        difficulty="Beginner",
        level="High School STEM (Grades 9-12)",
        domain="Medical Imaging",
        course_context="tell benign and malignant lesions apart",
        subject="Intro to Medical AI",
        topic_focus="Skin Lesion Classification",
        estimated_days=3,
        resources=[{"name": "ISIC Dataset", "url": "https://example.org/isic"}],
    )

    problem = formulate_problem_statement(m, {}, fake_client, "deepseek-v4-flash")
    agent0_prompt = captured["messages"][1]["content"]
    qa_prompt = build_qa_prompt(m, problem, {})
    coder_prompt = build_exercise_prompt(m, problem, unit_test_code="def test_x(): pass")
    scaffold_prompt = build_scaffold_prompt(m, problem, "def run_pipeline(): return {}")
    slide_prompt = build_lesson_plan_prompt(m, problem, "def run_pipeline(): return {}", {})

    for prompt in (agent0_prompt, qa_prompt, coder_prompt, scaffold_prompt, slide_prompt):
        assert "Course Subject: Intro to Medical AI" in prompt
        assert "Domain: Medical Imaging" in prompt
        assert "Course Goal: tell benign and malignant lesions apart" in prompt
        assert "Core Topic Focus: Skin Lesion Classification" in prompt
        assert "Estimated Module Duration: 3 day(s)" in prompt
        assert "ISIC Dataset: https://example.org/isic" in prompt
