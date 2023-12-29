from rich import Console
from rich.progress import Progress, TextColumn


class ProgressCheckList:
    def __init__(
        self,
        idle_description: str,
        working_description: str,
        completed_description: str,
        console: Console = None,
    ):
        self.overall_progress = Progress(
            TextColumn("{task.description}"),
            console=console,
        )

        self.overall_progress_task = self.overall_progress.add_task(
            idle_description,
            total=None,
            start=False,
        )

    def add_item(
        self,
        idle_description: str,
        working_description: str,
        completed_description: str,
    ):
        pass