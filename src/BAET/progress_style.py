from collections.abc import Generator, Mapping
from typing import Any

from rich.console import Console, ConsoleOptions, RenderResult
from rich.repr import Result
from rich.style import Style
from rich.text import Text

from BAET._theme import app_theme
from BAET.progress_status import ProgressStatus, ProgressStatusLiteral, ProgressStatusType


def parse_style(style: Style | str) -> Style:
    if isinstance(style, Style):
        return style

    return Style.parse(style)


class ProgressStyle:
    def __init__(
        self,
        style_dict: dict[ProgressStatusType, str | Style] | None = None,
        *,
        waiting_style: str | Style | None = None,
        running_style: str | Style | None = None,
        completed_style: str | Style | None = None,
        error_style: str | Style | None = None,
    ):
        default_style_dict: dict[ProgressStatus, Style] = {
            key: parse_style(value or default)
            for key, value, default in [
                (ProgressStatus.Waiting, waiting_style, "dim bright_white"),
                (ProgressStatus.Running, running_style, "bright_cyan"),
                (ProgressStatus.Completed, completed_style, "bright_green"),
                (ProgressStatus.Error, error_style, "bright_red"),
            ]
        }

        if style_dict is not None:
            parsed_styles = {ProgressStatus(key): parse_style(val) for key, val in style_dict.items()}

            default_style_dict.update(parsed_styles)

        self.style_dict: Mapping[ProgressStatus, Style] = default_style_dict

    def __call__(
        self,
        text: str,
        status: ProgressStatus | ProgressStatusLiteral,
        *args: Any,
        style: Style | None = None,
        **kwargs: Any,
    ) -> Text:
        return Text(
            text,
            self.style_dict[ProgressStatus(status)] + style,
            *args,
            **kwargs,
        )

    def __rich_repr__(self) -> Result:
        yield "style_dict", self.style_dict

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        with console.capture() as capture:
            console.print(self.style_dict)
        yield Text.from_ansi(capture.get())


if __name__ == "__main__":
    from rich.console import Group, group
    from rich.padding import Padding
    from rich.panel import Panel
    from rich.pretty import pprint

    console = Console(theme=app_theme)

    basic_style = ProgressStyle(
        {"Completed": "bold green", ProgressStatus.Error: "bold red"},
        running_style="italic bold cyan",
        waiting_style="underline yellow",
    )

    theme_style = ProgressStyle(
        {
            ProgressStatus.Waiting: app_theme.styles["status.waiting"],
            ProgressStatus.Running: app_theme.styles["status.running"],
            ProgressStatus.Completed: app_theme.styles["status.completed"],
            ProgressStatus.Error: app_theme.styles["status.error"],
        },
    )

    @group()
    def apply_styles(style: ProgressStyle, message: str) -> Generator[Text, Any, None]:
        for status in ["Waiting", "Completed", "Running", "Error"]:
            yield style(message.format(status), status)  # type: ignore

    @group()
    def make_style_group(style: ProgressStyle, message: str) -> Generator[Text, Any, None]:
        with console.capture() as pretty_capture:
            pprint(
                {key.value: val.color.name for key, val in style.style_dict.items() if val.color},
                console=console,
                expand_all=True,
                indent_guides=False,
            )
        with console.capture() as repr_capture:
            console.print(
                style,
                "\n[u]Demo Application:[/]",
                Padding(apply_styles(style, message), pad=(0, 0, 0, 3)),
            )

        yield Text.from_ansi(f"Input Style: {pretty_capture.get()}\n")
        yield Text.from_ansi(f"Resulting ProgressStyle: {repr_capture.get()}")

    layout = Group(
        Panel(
            make_style_group(basic_style, "This is the style for ProgressStyle.{0}"),
            title="[bold green]Basic Style",
        ),
        Panel(
            make_style_group(
                theme_style,
                'This is the style for "ProgressStyle.{0}", taken from app_theme in BAET',
            ),
            title="[bold green]Theme Style",
        ),
    )

    console.print(layout)
