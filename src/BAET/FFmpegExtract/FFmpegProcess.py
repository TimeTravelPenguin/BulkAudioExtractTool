from fractions import Fraction

import ffmpeg
from rich.progress import Progress

from BAET.Console import console, error_console
from BAET.Logging import info_logger


class ProbedOutput:
    def __init__(self, ffmpeg_output, stream: dict):
        self.output = ffmpeg_output
        self.stream = stream

    def get_stream_index(self):
        return self.stream["index"]


class FFmpegProcess:
    def __init__(
        self,
        output,
        probe_stream,
        overwrite: bool,
    ):
        self.ffmpeg_output = output.global_args("-progress", "-", "-nostats")
        self.probe_stream = probe_stream
        self.overwrite = overwrite

    def run_synchronously(self, progress_handle) -> None:
        proc = ffmpeg.run_async(
            self.ffmpeg_output,
            overwrite_output=self.overwrite,
            pipe_stdout=True,
            pipe_stderr=True,
        )

        try:
            while proc.poll() is None:
                output = proc.stdout.readline().decode("utf-8").strip()
                if "out_time_ms" in output:
                    val = output.split("=", 1)[1]
                    progress_handle(
                        float(val) / 1_000_000,
                        desc=f"Stream index: {self.probe_stream['index']}",
                    )

            if proc.returncode != 0:
                # TODO
                raise Exception("Unknown Error")
        except Exception as e:
            info_logger.critical("%s: %s", type(e).__name__, e)
            error_console.print_exception()
            raise e


class FFmpegProcessGroup:
    def __init__(
        self,
        probed_outputs: list[ProbedOutput],
        overwrite: bool,
    ):
        self.outputs = [
            FFmpegProcess(
                output.output,
                output.stream,
                overwrite,
            )
            for output in probed_outputs
        ]

    def run_synchronously(self) -> None:
        with Progress(console=console) as progress:
            for output in self.outputs:
                task = progress.add_task(
                    f"Preparing...",
                    total=float(output.probe_stream["duration_ts"])
                    * float(Fraction(output.probe_stream["time_base"])),
                )

                def update_task(prog: int, desc: str | None = None):
                    progress.update(
                        task, completed=prog, description=desc, refresh=True
                    )

                output.run_synchronously(update_task)