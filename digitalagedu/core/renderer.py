import os
from jinja2 import Environment, FileSystemLoader


class TemplateRenderer:
    def __init__(self):
        # Get the directory where renderer.py is located
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Templates are located at ../templates relative to core/renderer.py
        template_dir = os.path.join(os.path.dirname(current_dir), "templates")
        
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=False
        )

    def render(self, template_name: str, context: dict):
        template = self.env.get_template(template_name)
        return template.render(context)
