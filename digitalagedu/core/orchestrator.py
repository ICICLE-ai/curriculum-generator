from digitalagedu.core.config import load_config
from digitalagedu.core.curriculum_service import CurriculumService
from digitalagedu.core.renderer import TemplateRenderer
from digitalagedu.core.writer import FileWriter


class CurriculumEngine:
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.service = CurriculumService(self.config)
        self.renderer = TemplateRenderer()
        self.writer = FileWriter()

    def run(self):
        # Step 1: Transform config → structured lesson data
        lesson_data = self.service.build()

        # Step 2: Render template
        rendered_output = self.renderer.render(
            template_name="lesson_plan.md.j2",
            context=lesson_data
        )

        # Step 3: Write to file
        self.writer.write(
            content=rendered_output,
            output_path=f"output/curriculum_grade_{self.config.curriculum.grade}.md"
        )
