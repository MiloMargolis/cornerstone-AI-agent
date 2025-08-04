import os
from jinja2 import Environment, FileSystemLoader


class PromptLoader:
    def __init__(self, template_dir=None):
        """Initialize the prompt loader with the directory containing prompt templates."""
        if template_dir is None:
            # Get absolute path to prompts directory relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            template_dir = os.path.join(current_dir, "prompts")
            template_dir = os.path.abspath(template_dir)

        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=True)

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(context)
