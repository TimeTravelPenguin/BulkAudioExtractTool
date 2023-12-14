from rich.console import Console
from rich.progress import Progress, TextColumn

from .progress_status import ProgressStatus
from .progress_style import ProgressStyle


class ProgressCheckList:
    def __init__(
        self,
        waiting_description: str,
        running_description: str,
        completed_description: str,
        error_description: str,
        progress_style: ProgressStyle | None = None,
        console: Console | None = None,
    ):
        self.descriptions: dict[ProgressStatus, str] = {
            ProgressStatus.Waiting: waiting_description,
            ProgressStatus.Running: running_description,
            ProgressStatus.Completed: completed_description,
            ProgressStatus.Error: error_description,
        }

        self.progress_style = progress_style or ProgressStyle()

        self.overall_progress = Progress(
            TextColumn("{task.description}"),
            console=console,
        )

        self.overall_progress_task = self.overall_progress.add_task(
            waiting_description,
            total=None,
            start=False,
        )

    def add_item(
        self,
        waiting_description: str,
        running_description: str,
        completed_description: str,
        error_description: str,
    ) -> None:
        # TODO
        pass
