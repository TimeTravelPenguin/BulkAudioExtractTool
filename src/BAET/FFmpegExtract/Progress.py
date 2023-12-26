import ffmpeg
from rich.progress import MofNCompleteColumn, Progress, TaskID, TextColumn
from rich.table import Table

from BAET.Console import console, error_console
from BAET.FFmpegExtract import IndexedOutputs, StreamIndex
from BAET.FFmpegExtract.Extractor import FFmpegWorker
from BAET.Logging import info_logger


__all__ = ["FFmpegProgress"]


class FFmpegProgress:
    def __init__(self, worker: FFmpegWorker):
        self.job = worker.job
        self.indexed_outputs: IndexedOutputs = worker.indexed_outputs

        self.display: Table = Table(show_header=False, padding=(0, 5)).grid()

        self.overall_progress: Progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            MofNCompleteColumn(),
            console=console,
        )

        self.overall_progress_task = self.overall_progress.add_task(
            description=f'Preparing to extract audio from "{self.job.input_file.name}"',
            total=len(self.job.audio_streams),
            start=False,
        )

        self.sub_progress: Progress = Progress(
            TextColumn("  "),
            *Progress.get_default_columns(),
            console=console,
        )

        self.sub_progress_tasks: list[tuple[StreamIndex, TaskID]] = []
        for idx, stream in enumerate(self.job.audio_streams, start=1):
            stream_index = stream["index"]
            task = self.overall_progress.add_task(
                description=f"Extracting stream: {idx}/{len(self.job.audio_streams)}",
                total=self.job.get_duration_ms(stream_index),
                start=False,
            )

            self.sub_progress_tasks.append((stream_index, task))

        self.display.add_row(self.overall_progress)
        self.display.add_row(self.sub_progress)

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