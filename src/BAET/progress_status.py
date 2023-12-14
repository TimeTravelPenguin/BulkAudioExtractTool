from __future__ import annotations

from enum import StrEnum
from typing import Literal, TypeAlias

from rich.console import Console, ConsoleOptions, RenderResult
from rich.repr import Result

ProgressStatusLiteral: TypeAlias = Literal["Waiting", "Running", "Completed", "Error"]


class ProgressStatus(StrEnum):
    Waiting = "Waiting"
    Running = "Running"
    Completed = "Completed"
    Error = "Error"

    def __rich_repr__(self) -> Result:
        yield repr(self)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield repr(self)


ProgressStatusType: TypeAlias = ProgressStatus | ProgressStatusLiteral

if __name__ == "__main__":
    import rich

    waiting = ProgressStatus("Waiting")
    completed = ProgressStatus(ProgressStatus.Completed)

    rich.print(waiting)
    rich.print(completed)
