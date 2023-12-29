from collections.abc import Mapping

from rich.console import Console, ConsoleOptions, RenderResult
from rich.repr import Result
from rich.style import Style
from rich.text import Text

from BAET._theme import app_theme
from BAET.progress_status import ProgressStatus, ProgressStatusLiteral


def parse_style(style: Style | str) -> Style:
    if isinstance(style, Style):
        return style

    return Style.parse(style)


class ProgressStyle:
    def __init__(
        self,
        style_dict: dict[ProgressStatusLiteral | ProgressStatus, str | Style]
        | None = None,
        *,
        waiting_style: str | Style | None = None,
        running_style: str | Style | None = None,
        completed_style: str | Style | None = None,
        error_style: str | Style | None = None,
        current_status: ProgressStatusLiteral | ProgressStatus = ProgressStatus.Waiting,
    ):
        default_style_dict: dict[ProgressStatus, Style] = {
            key: parse_style(value or default)
            for key, value, default in [
                (ProgressStatus.Waiting, waiting_style, "white"),
                (ProgressStatus.Running, running_style, "blue"),
                (ProgressStatus.Completed, completed_style, "green"),
                (ProgressStatus.Error, error_style, "red"),
            ]
        }

        if style_dict is not None:
            parsed_styles = {
                ProgressStatus(key): parse_style(val) for key, val in style_dict.items()
            }

            default_style_dict.update(parsed_styles)

        self.style_dict: Mapping[ProgressStatus, Style] = default_style_dict
        self.current_status = current_status

    def __call__(self, text: str, *args, **kwargs) -> Text:
        text = Text(
            text=text,
            style=self.style_dict[self.current_status],
            *args,
            **kwargs,
        )

        return text

    @property
    def current_status(self) -> ProgressStatus:
        return self._current_status

    @current_status.setter
    def current_status(self, status: ProgressStatusLiteral | ProgressStatus):
        self._current_status = ProgressStatus(status)

    def __rich_repr__(self) -> Result:
        yield f"current_status: {self.current_status}"
        yield "style_dict", self.style_dict

    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        out = {"current_status": self.current_status, **self.style_dict}
        with console.capture() as capture:
            console.print(out)
        yield Text.from_ansi(capture.get())


if __name__ == "__main__":
    from rich.console import Group, group, Console
    from rich.pretty import pprint
    from rich.text import Text
    from rich.panel import Panel
    from rich.padding import Padding

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
        current_status="Running",
    )

    @group()
    def apply_styles(style: ProgressStyle, message: str):
        for status in ["Waiting", "Completed", "Running", "Error"]:
            style.current_status = status
            yield style(message.format(status))

    @group()
    def make_style_group(style: ProgressStyle, message: str):
        with console.capture() as pretty_capture:
            pprint(
                {key.value: val.color.name for key, val in style.style_dict.items()},
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