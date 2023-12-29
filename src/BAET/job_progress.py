import ffmpeg
from bidict import bidict
from rich.console import ConsoleRenderable, Group
from rich.padding import Padding
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from BAET._aliases import StreamTaskBiMap
from BAET._console import app_console, error_console
from BAET._logging import console_logger
from BAET.jobs import FFmpegJob


class FFmpegJobProgress(ConsoleRenderable):
    # TODO: Need mediator to consumer/producer printing
    def __init__(self, job: FFmpegJob):
        self.job = job

        bar_blue = "#5079AF"
        bar_yellow = "#CAAF39"

        self.overall_progress = Progress(
            TextColumn("Progress for {task.fields[filename]}"),
            BarColumn(
                complete_style=bar_blue,
                finished_style="green",
                pulse_style=bar_yellow,
            ),
            TextColumn("Completed {task.completed} of {task.total}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=app_console,
        )

        self.overall_progress_task = self.overall_progress.add_task(
            "Waiting...",
            start=False,
            filename=job.input_file.name,
            total=len(self.job.audio_streams),
        )

        self.stream_task_progress = Progress(
            TextColumn("Audio Stream {task.fields[stream_index]}"),
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

        self.stream_task_bimap: StreamTaskBiMap = bidict()

        stream_task_bimap = bidict()
        for stream in self.job.audio_streams:
            stream_index = stream["index"]

            task = self.stream_task_progress.add_task(
                "Waiting...",
                start=False,
                total=self.job.stream_duration_ms(stream),
                stream_index=stream_index,
                status="Waiting",
            )

            stream_task_bimap[stream_index] = task

        self.stream_task_bimap = stream_task_bimap

        self.display = Group(
            self.overall_progress,
            Padding(self.stream_task_progress, (1, 0, 2, 5)),
        )

    def start(self):
        self.overall_progress.start_task(self.overall_progress_task)
        for task in self.stream_task_bimap.values():
            self.stream_task_progress.start_task(task)
            self.stream_task_progress.update(task, status="Working")

            self.run_task(task)

            self.stream_task_progress.update(task, status="Done")
            self.stream_task_progress.stop_task(task)
            self.overall_progress.update(self.overall_progress_task, advance=1)

        self.overall_progress.stop_task(self.overall_progress_task)

    def run_task(self, task: TaskID):
        stream_index = self.stream_task_bimap.inverse[task]
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
                        self.stream_task_progress.update(
                            task,
                            completed=float(val),
                        )

            if p.returncode != 0:
                raise RuntimeError(p.stderr.read().decode("utf-8"))
        except Exception as e:
            console_logger.critical("%s: %s", type(e).__name__, e)
            error_console.print_exception()
            raise e