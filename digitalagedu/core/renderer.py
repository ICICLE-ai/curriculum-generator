from jinja2 import Environment, FileSystemLoader


class TemplateRenderer:
    def __init__(self):
        self.env = Environment(
            loader=FileSystemLoader("digitalagedu/templates"),
            autoescape=False
        )

    def render(self, template_name: str, context: dict):
        template = self.env.get_template(template_name)
        return template.render(context)
