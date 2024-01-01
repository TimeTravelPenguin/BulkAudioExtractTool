from rich.console import Console

from BAET._theme import app_theme

app_console = Console(theme=app_theme)
error_console = Console(stderr=True, style="bold red", theme=app_theme)
