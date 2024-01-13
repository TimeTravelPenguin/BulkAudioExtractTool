from typing import Final

from rich.theme import Theme

app_theme_dict: Final[dict[str, str]] = {
    "app.version": "italic bright_cyan",
    # TODO: Remove
    "argparse.arg_default": "dim italic",
    "argparse.arg_default_parens": "dim",
    "argparse.arg_default_value": "not italic bold dim",
    "argparse.help_keyword": "bold blue",
    "argparse.debug_todo": "reverse bold indian_red",
    # Help screen
    "keyword": "bold blue",
    "todo": "reverse bold indian_red",
    # Progress status
    "status.waiting": "dim bright_white",
    "status.running": "bright_cyan",
    "status.completed": "bright_green",
    "status.error": "bright_red",
}

app_theme = Theme(app_theme_dict)
