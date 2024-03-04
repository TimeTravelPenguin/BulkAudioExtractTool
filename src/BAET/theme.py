"""Theme options used by Rich library for the app."""

from typing import Final

from rich.theme import Theme

app_theme_dict: Final[dict[str, str]] = {
    "app.version": "italic bright_cyan",
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
