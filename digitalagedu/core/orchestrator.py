import re

from digitalagedu.core.config import load_config
from digitalagedu.core.curriculum_service import CurriculumService
from digitalagedu.core.renderer import CurriculumMarkdownRenderer
from digitalagedu.core.writer import FileWriter


class CurriculumEngine:
    def __init__(self, config_path: str):
        self.config = load_config(config_path)
        self.service = CurriculumService(self.config)
        self.renderer = CurriculumMarkdownRenderer()
        self.writer = FileWriter()

    def run(self):
        # Step 1: Transform config → structured lesson data
        lesson_data = self.service.build()

        # Step 2: Render markdown syllabus
        rendered_output = self.renderer.render(lesson_data)

        level_slug = re.sub(r"\W+", "_", self.config.curriculum.level).strip("_")
        self.writer.write(
            content=rendered_output,
            output_path=f"output/curriculum_{level_slug}.md"
        )
