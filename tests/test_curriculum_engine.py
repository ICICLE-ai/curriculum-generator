import unittest
import os
import tempfile
import yaml
from digitalagedu import (
    load_config,
    RootConfig,
    CurriculumConfig,
    Topic,
    CurriculumEngine,
    CurriculumService,
    TemplateRenderer,
    FileWriter,
    generate_llm_curriculum,
)
from digitalagedu.core.llm.schemas import (
    Module,
    ProblemStatementSchema,
    SlideDeckSchema,
    ExerciseSolutionSchema,
    UnitTestSchema,
    ValidatedExerciseSchema,
)
from digitalagedu.core.llm.context import (
    build_system_prompt,
    build_slide_prompt,
    build_exercise_prompt,
    build_qa_prompt,
)


class TestCurriculumEngineAndLLM(unittest.TestCase):

    def test_imports_clean(self):
        """Verify all core symbols and LLM entry points import cleanly without templates."""
        self.assertIsNotNone(load_config)
        self.assertIsNotNone(CurriculumEngine)
        self.assertIsNotNone(CurriculumService)
        self.assertIsNotNone(TemplateRenderer)
        self.assertIsNotNone(generate_llm_curriculum)

    def test_template_renderer_embedded(self):
        """Verify TemplateRenderer works out-of-the-box using embedded default template."""
        renderer = TemplateRenderer()
        context = {
            "subject": "Intro to Medical AI",
            "grade": "10",
            "weeks": 4,
            "topics": [
                {
                    "name": "Image Preprocessing",
                    "description": "Pixel normalization",
                    "project": "Skin Lesion Classifier",
                    "activities": ["NumPy basics", "Histogram equalization"],
                    "weeks": {
                        "Week_01": ["NumPy basics"]
                    }
                }
            ],
            "global_resources": [
                {"name": "PyTorch Docs", "url": "https://pytorch.org"}
            ]
        }
        rendered = renderer.render("lesson_plan.md.j2", context)
        self.assertIn("# Intro to Medical AI Curriculum", rendered)
        self.assertIn("Grade: 10", rendered)
        self.assertIn("Duration: 4 weeks", rendered)
        self.assertIn("## Image Preprocessing", rendered)
        self.assertIn("PyTorch Docs", rendered)

    def test_curriculum_service_and_engine(self):
        """Verify CurriculumService builds data and CurriculumEngine executes."""
        sample_config_data = {
            "project": {
                "domain": "Medical Vision",
                "context_statement": "Skin cancer classification"
            },
            "dataset": {
                "root_path": "."
            },
            "output": {
                "directory": "./output_test"
            },
            "curriculum": {
                "subject": "Dermatology AI",
                "grade": 11,
                "weeks": 4,
                "topics": [
                    {
                        "name": "CNN Foundations",
                        "description": "Learn 2D convolutions",
                        "project": "Lesion Classifier"
                    }
                ]
            }
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(sample_config_data, f)
            config_path = f.name

        try:
            config = load_config(config_path)
            self.assertEqual(config.curriculum.subject, "Dermatology AI")
            
            service = CurriculumService(config)
            lesson_data = service.build()
            self.assertEqual(lesson_data["subject"], "Dermatology AI")
            self.assertEqual(lesson_data["grade"], 11)

            engine = CurriculumEngine(config_path)
            rendered = engine.renderer.render("lesson_plan.md.j2", lesson_data)
            self.assertIn("Dermatology AI", rendered)
        finally:
            if os.path.exists(config_path):
                os.remove(config_path)

    def test_llm_schemas_and_prompts(self):
        """Verify LLM schemas instantiate and context prompt builders function properly."""
        sys_prompt = build_system_prompt()
        self.assertIn("You are an expert deep learning educator", sys_prompt)

        mod = Module(
            id="test_module",
            title="Transfer Learning",
            week=1,
            context="Fine-tune ResNet on skin lesions",
            difficulty="intermediate"
        )
        slide_prompt = build_slide_prompt(mod)
        self.assertIn("Transfer Learning", slide_prompt)

        exercise_prompt = build_exercise_prompt(mod)
        self.assertIn("Transfer Learning", exercise_prompt)

        qa_prompt = build_qa_prompt(mod, solution_code="import torch\ndef model(): pass")
        self.assertIn("test_module_solution", qa_prompt)


if __name__ == "__main__":
    unittest.main()
