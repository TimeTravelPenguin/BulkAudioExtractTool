import ffmpeg
from bidict import MutableBidirectionalMapping, bidict
from rich.console import Console, ConsoleOptions, ConsoleRenderable, Group, RenderResult
from rich.highlighter import ReprHighlighter
from rich.padding import Padding
from rich.progress import BarColumn, Progress, TaskID, TextColumn, TimeElapsedColumn, TimeRemainingColumn

from ._aliases import StreamTaskBiMap
from ._console import app_console
from ._logging import create_logger
from .jobs import FFmpegJob

logger = create_logger()


class FFmpegJobProgress(ConsoleRenderable):
    # TODO: Need mediator to consumer/producer printing
    def __init__(self, job: FFmpegJob):
        self.job = job

        bar_blue = "#5079AF"
        bar_yellow = "#CAAF39"

        self._overall_progress = Progress(
            TextColumn('Progress for "{task.fields[filename]}"', highlighter=ReprHighlighter()),
            BarColumn(
                complete_style=bar_blue,
                finished_style="green",
                pulse_style=bar_yellow,
            ),
            TextColumn("Completed {task.completed} of {task.total}", highlighter=ReprHighlighter()),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=app_console,
        )

        self._overall_progress_task = self._overall_progress.add_task(
            "Waiting...",
            start=False,
            filename=job.input_file.name,
            total=len(self.job.audio_streams),
        )

        self._stream_task_progress = Progress(
            TextColumn("Audio stream {task.fields[stream_index]}", highlighter=ReprHighlighter()),
            BarColumn(
                complete_style=bar_blue,
                finished_style="green",
                pulse_style=bar_yellow,
            ),
            TextColumn("{task.fields[status]}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=app_console,
        )

        self._stream_task_bimap: StreamTaskBiMap = bidict()

        stream_task_bimap: MutableBidirectionalMapping[int, TaskID] = bidict()
        for stream in self.job.audio_streams:
            stream_index = stream["index"]

            task = self._stream_task_progress.add_task(
                "Waiting...",
                start=False,
                total=self.job.stream_duration_ms(stream),
                stream_index=stream_index,
                status="[plum4]Waiting[/]",
            )

            stream_task_bimap[stream_index] = task

        self._stream_task_bimap = stream_task_bimap

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield Group(
            self._overall_progress,
            Padding(self._stream_task_progress, (1, 0, 1, 5)),
        )

    def _run_task(self, task: TaskID) -> None:
        stream_index: int = self._stream_task_bimap.inverse[task]

        logger.info(f"Extracting audio stream {stream_index} of {self.job.input_file.name}")

        output = self.job.indexed_outputs[stream_index]

        proc = ffmpeg.run_async(
            output,
            pipe_stdout=True,
            pipe_stderr=True,
        )

        try:
            with proc as p:
                for line in p.stdout:
                    decoded = line.decode("utf-8").strip()
                    if "out_time_ms" in decoded:
                        val = decoded.split("=", 1)[1]
                        self._stream_task_progress.update(
                            task,
                            completed=float(val),
                        )

            if p.returncode != 0:
                raise RuntimeError(p.stderr.read().decode("utf-8"))

        except RuntimeError as e:
            logger.critical("%s: %s", type(e).__name__, e)
            raise e

    def start(self) -> None:
        self._overall_progress.start_task(self._overall_progress_task)
        logger.info(f"Stream index to job task ID bimap: {self._stream_task_bimap}")
        for task in self._stream_task_bimap.values():
            self._stream_task_progress.start_task(task)

            self._stream_task_progress.update(task, status="[italic cornflower_blue]Working[/]")

            try:
                self._run_task(task)
                self._stream_task_progress.update(task, status="[bold green]Complete[/]")
            except RuntimeError as e:
                self._stream_task_progress.update(task, status="[bold red]ERROR[/]")
            finally:
                self._stream_task_progress.stop_task(task)
                self._overall_progress.advance(self._overall_progress_task, advance=1)

        self._overall_progress.stop_task(self._overall_progress_task)
