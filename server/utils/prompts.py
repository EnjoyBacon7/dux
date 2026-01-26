"""
Shared utility for loading prompt templates.
"""
from pathlib import Path


def load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        template_name: Name of the template file (without .txt extension)

    Returns:
        Template content as string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    prompts_dir = Path(__file__).parent.parent / "prompts"
    template_path = prompts_dir / f"{template_name}.txt"

    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    return template_path.read_text(encoding="utf-8")
