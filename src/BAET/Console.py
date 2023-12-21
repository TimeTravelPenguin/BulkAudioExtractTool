from rich.console import Console

from BAET.Theme import app_theme

console = Console(theme=app_theme)
error_console = Console(stderr=True, style="bold red")
