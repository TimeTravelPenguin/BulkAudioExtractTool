from __future__ import annotations

from enum import StrEnum
from typing import Literal

import rich.repr


type ProgressStatusLiteral = Literal["Waiting", "Running", "Completed", "Error"]


@rich.repr.auto
class ProgressStatus(StrEnum):
    Waiting = "Waiting"
    Running = "Running"
    Completed = "Completed"
    Error = "Error"


if __name__ == "__main__":
    import rich

    waiting = ProgressStatus("Waiting")
    completed = ProgressStatus(ProgressStatus.Completed)

    rich.print(waiting)
    rich.print(completed)