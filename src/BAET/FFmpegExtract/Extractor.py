from collections.abc import MutableMapping

import ffmpeg
from bidict import bidict
from ffmpeg import Stream
from rich.console import Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table

from BAET.AppArgs import AppArgs
from BAET.Console import app_console, error_console
from BAET.FFmpegExtract.Aliases import StreamIndex
from BAET.FFmpegExtract.Jobs import FFmpegJob, FFmpegJobFactory
from BAET.Logging import info_logger

__all__ = ["FFmpegExtractor"]

type StreamTaskMap = MutableMapping[StreamIndex, TaskID]
type JobProgressMap = MutableMapping[FFmpegJob, Progress]
type JobTaskMap = MutableMapping[FFmpegJob, TaskID]
type JobOutputMap = MutableMapping[FFmpegJob, Stream]


class FFmpegExtractor:
    def __init__(self, app_args: AppArgs):
        self.args = app_args

        job_factory = FFmpegJobFactory(
            app_args.input_dir,
            app_args.output_dir,
            app_args.input_filters,
            app_args.output_configuration,
        )

        # TODO: This is weird
        self.jobs = list(job_factory)

    def run_synchronously(self):
        progress_bars = [JobProgress(job) for job in self.jobs]
        group = Group(*[progress_bar.display for progress_bar in progress_bars])

        with Live(group):
            for progress in progress_bars:
                # info_logger.info("Processing input file '%s'", progress.job.input_file)
                progress.start()


class JobProgress:
    # TODO: Need mediator to consumer/producer printing
    def __init__(self, job: FFmpegJob):
        self.job = job

        self.overall_progress = Progress(
            TextColumn("Progress for {task.fields[filename]}"),
            BarColumn(),
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
            BarColumn(),
            TextColumn("{task.fields[status]}"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=app_console,
        )

        self.stream_task_bimap: StreamTaskMap = bidict()

        for stream in self.job.audio_streams:
            stream_index = stream["index"]

            task = self.stream_task_progress.add_task(
                "Waiting...",
                start=False,
                total=self.job.stream_duration_ms(stream),
                stream_index=stream_index,
                status="Waiting",
            )

            self.stream_task_bimap[stream_index] = task

        self.display = Group(
            self.overall_progress,
            Panel(self.stream_task_progress, title="Stream Extraction"),
        )

    def start(self):
        self.overall_progress.start()
        for stream_index, task in self.stream_task_bimap.items():
            self.stream_task_progress.start_task(task)
            self.stream_task_progress.update(task, status="Working")
            output = self.job.indexed_outputs[stream_index]

            proc = ffmpeg.run_async(
                output,
                pipe_stdout=True,
                pipe_stderr=True,
            )

            try:
                while proc.poll() is None:
                    output = proc.stdout.readline().decode("utf-8").strip()
                    if "out_time_ms" in output:
                        val = output.split("=", 1)[1]
                        self.stream_task_progress.update(
                            task,
                            completed=float(val),
                        )

                if proc.returncode != 0:
                    raise RuntimeError(proc.stderr.read().decode("utf-8"))
            except Exception as e:
                info_logger.critical("%s: %s", type(e).__name__, e)
                error_console.print_exception()
                raise e

            self.stream_task_progress.update(task, status="Done")
            self.stream_task_progress.stop_task(task)
            self.overall_progress.update(self.overall_progress_task, advance=1)
        self.overall_progress.stop()


class FFmpegProgress:
    def __init__(self, jobs: list[FFmpegJob]):
        self.job_progress = dict({job: JobProgress(job) for job in jobs})

        self.display: Table = Table(show_header=False, padding=(0, 5)).grid()
        for progress in self.job_progress.values():
            self.display.add_row(progress.display)

    def _add_job(self, job: FFmpegJob):
        ...

    def iter_tasks(self):
        """
        Iterate over each subtask.

        Returns:
            An iterator yielding (`task_id`, `update_handler(total, *args, **kwargs)`) for each subtask.
        """
        self.overall_progress.start_task(self.overall_progress_task)

        for stream_index, task in self.sub_progress_tasks:

            def update_handle(total: float, *args, **kwargs):
                self.sub_progress.update(task, total=total, *args, **kwargs)

            self.overall_progress.start_task(task)
            yield stream_index, task, update_handle
            self.overall_progress.stop_task(task)

        self.overall_progress.stop_task(self.overall_progress_task)

    def start(self):
        self.overall_progress.start()
        self.sub_progress.start()

    def stop(self):
        self.overall_progress.stop()
        self.sub_progress.stop()

    def run_tasks_synchronously(self):
        for stream_index, task, handle in self.iter_tasks():
            output = self.indexed_outputs[stream_index]

            proc = ffmpeg.run_async(
                output,
                pipe_stdout=True,
                pipe_stderr=True,
            )

            try:
                while proc.poll() is None:
                    output = proc.stdout.readline().decode("utf-8").strip()
                    if "out_time_ms" in output:
                        val = output.split("=", 1)[1]
                        handle(
                            float(val),
                            # desc=f"Stream index: {stream_index}",
                        )

                if proc.returncode != 0:
                    # TODO
                    raise Exception("Unknown Error")
            except Exception as e:
                info_logger.critical("%s: %s", type(e).__name__, e)
                error_console.print_exception()
                raise e
