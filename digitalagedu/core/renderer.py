import os
from jinja2 import Environment, FileSystemLoader


class TemplateRenderer:
    """
    Renders curriculum syllabus and lesson plans to Markdown using Jinja2 templates.
    """

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_dir = os.path.join(os.path.dirname(current_dir), "templates")

        self.template_dir = template_dir
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=False
        )

    def render(self, template_name: str = "lesson_plan.md.j2", context: dict = None) -> str:
        if context is None and isinstance(template_name, dict):
            context = template_name
            template_name = "lesson_plan.md.j2"
        template = self.env.get_template(template_name)
        return template.render(context or {})
