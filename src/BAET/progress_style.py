from collections.abc import Mapping

from rich.repr import Result
from rich.style import Style
from rich.text import Text

from .progress_status import ProgressStatus, ProgressStatusLiteral


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
            ProgressStatus.Waiting: parse_style(waiting_style or "white"),
            ProgressStatus.Running: parse_style(running_style or "blue"),
            ProgressStatus.Waiting.Completed: parse_style(completed_style or "green"),
            ProgressStatus.Waiting.Error: parse_style(error_style or "red"),
        }

        if style_dict is not None:
            parsed_styles = {
                ProgressStatus(key): parse_style(val) for key, val in style_dict.items()
            }

            default_style_dict.update(parsed_styles)

        self.style_dict: Mapping[ProgressStatus, Style] = default_style_dict
        self._current_status: ProgressStatus = ProgressStatus(current_status)

    @property
    def current_status(self) -> ProgressStatus:
        return self._current_status

    @current_status.setter
    def current_status(self, status: ProgressStatusLiteral | ProgressStatus):
        self._current_status = ProgressStatus(status)

    def __call__(self, text: str, *args, **kwargs) -> Text:
        text = Text(
            text=text,
            style=self.style_dict[self._current_status],
            *args,
            **kwargs,
        )

        return text

    def __rich_repr__(self) -> Result:
        yield "_current_status", self._current_status
        yield "style_dict", self.style_dict


if __name__ == "__main__":
    import rich

    style = ProgressStyle(
        {"Completed": "bold green", ProgressStatus.Error: "bold red"},
        running_style="italic bold cyan",
        waiting_style="underline yellow",
    )

    for status in ["Waiting", "Completed", "Running", "Error"]:
        style.current_status = status
        rich.print(style(f'This is the style for "{status}"'))