"""Help configuration for the CLI."""

from collections.abc import Callable
from functools import wraps
from typing import Any

import rich_click as click
from rich_click import RichHelpConfiguration
from rich_click.rich_help_configuration import OptionHighlighter

from BAET._config.console import app_console


def baet_config(
    show_arguments: bool = True,
    column_width_ratio: tuple[None, None] | tuple[int, int] = (None, None),
    use_markdown: bool = False,
    use_markdown_emoji: bool = True,
    use_rich_markup: bool = True,
) -> Any:
    """Decorator for BAET help config."""

    def wrapper(func: Callable[..., Any]) -> Any:
        @click.rich_config(
            console=app_console,
            help_config=RichHelpConfiguration(
                show_arguments=show_arguments,
                style_commands_table_column_width_ratio=column_width_ratio,
                use_markdown=use_markdown,
                use_markdown_emoji=use_markdown_emoji,
                use_rich_markup=use_rich_markup,
                style_helptext="not dim bright_white",
                highlighter=OptionHighlighter(),
            ),
        )
        @wraps(func)
        def inner(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)

        return inner

    return wrapper
