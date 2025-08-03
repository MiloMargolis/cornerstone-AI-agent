from jinja2 import Environment, FileSystemLoader

class PromptLoader:
    def __init__(self, template_dir="prompts"):
        """Initialize the prompt loader with the directory containing prompt templates."""
        self.env = Environment(loader=FileSystemLoader(template_dir), autoescape=False)

    def render(self, template_name: str, context: dict) -> str:
        template = self.env.get_template(template_name)
        return template.render(context)