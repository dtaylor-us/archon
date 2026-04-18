from __future__ import annotations

import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

_PROMPTS_DIR = Path(__file__).parent

_env = Environment(
    loader=FileSystemLoader(str(_PROMPTS_DIR)),
    autoescape=False,
    keep_trailing_newline=True,
)


def load_prompt(template_name: str, **kwargs: object) -> str:
    """Load and render a Jinja2 prompt template.

    Args:
        template_name: Name of the template (without .j2 extension).
        **kwargs: Variables to render into the template.

    Returns:
        The rendered prompt string.

    Raises:
        FileNotFoundError: If the template file does not exist.
    """
    try:
        template = _env.get_template(f"{template_name}.j2")
    except TemplateNotFound:
        raise FileNotFoundError(
            f"Prompt template '{template_name}.j2' not found in {_PROMPTS_DIR}"
        )
    return template.render(**kwargs)
