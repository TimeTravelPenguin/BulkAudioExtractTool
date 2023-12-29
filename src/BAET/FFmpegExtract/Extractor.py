from collections.abc import MutableMapping

import ffmpeg
from bidict import MutableBidict, bidict
from ffmpeg import Stream
from rich.console import Group
from rich.live import Live
from rich.padding import Padding
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

type StreamTaskBiMap = MutableBidict[StreamIndex, TaskID]
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
        job_progresses = [JobProgress(job) for job in self.jobs]
        group = Group(*[job_progress.display for job_progress in job_progresses])

        with Live(group):
            for progress in job_progresses:
                # info_logger.info("Processing input file '%s'", progress.job.input_file)
                progress.start()


class JobProgress:
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
                Padding(self.stream_task_progress, (1, 0, 2, 5)),
            )

        # self.display = Group(
        #     self.overall_progress,
        #     Padding(
        #         Panel(
        #             self.stream_task_progress, title="Stream Extraction", expand=False
        #         ),
        #         (0, 0, 1, 3),
        #     ),
        # )

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
            info_logger.critical("%s: %s", type(e).__name__, e)
            error_console.print_exception()
            raise e


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