import contextlib
from fractions import Fraction
from pathlib import Path
from typing import Iterator, TypeAlias

import ffmpeg
import rich
from ffmpeg import Stream
from rich.console import Group
from rich.progress import MofNCompleteColumn, Progress, TaskID, TextColumn
from rich.table import Table

from BAET.AppArgs import AppArgs
from BAET.Console import console, error_console
from BAET.Logging import info_logger

StreamIndex: TypeAlias = int
IndexedOutputs: TypeAlias = dict[StreamIndex, Stream]

VIDEO_EXTENSIONS = [".mp4", ".mkv"]


@contextlib.contextmanager
def probe_audio_streams(file: Path) -> Iterator[list[dict]]:
    try:
        info_logger.info('Probing "%s"', file)
        probe = ffmpeg.probe(file)

        audio_streams = sorted(
            [
                stream
                for stream in probe["streams"]
                if "codec_type" in stream and stream["codec_type"] == "audio"
            ],
            key=lambda stream: stream["index"],
        )

        if not audio_streams:
            raise ValueError("No audio streams found")

        info_logger.info("Found %d audio streams", len(audio_streams))
        yield audio_streams

    except (ffmpeg.Error, ValueError) as e:
        info_logger.critical("%s: %s", type(e).__name__, e)
        error_console.print_exception()
        raise e


class FFmpegJob:
    def __init__(self, input_file: Path, audio_streams: list[dict]):
        self.input_file: Path = input_file
        self.audio_streams: list[dict] = audio_streams
        self.durations_ms_dict: dict[int, float] = {
            stream["index"]: 1_000_000
            * float(stream["duration_ts"])
            * float(Fraction(stream["time_base"]))
            for stream in audio_streams
        }

    def get_duration_ms(self, stream_idx) -> float:
        stream = next(
            iter(
                [
                    stream
                    for stream in self.audio_streams
                    if stream["index"] == stream_idx
                ]
            ),
            None,
        )

        if stream is None:
            raise IndexError("Stream_index not found")

        return (
            1_000_000
            * float(stream["duration_ts"])
            * float(Fraction(stream["time_base"]))
        )


class FFmpegWorker:
    def __init__(self, job: FFmpegJob, indexed_outputs: IndexedOutputs):
        self.job = job
        self.indexed_outputs: IndexedOutputs = indexed_outputs


class FFmpegJobFactory:
    def __init__(self, app_args: AppArgs):
        self.app_args = app_args

    def get_files(self) -> list[Path]:
        files = []

        for file in self.app_args.input_dir.iterdir():
            if file.suffix not in VIDEO_EXTENSIONS:
                continue

            if file.is_file() and self.app_args.input_filters.include.match(file.name):
                if not self.app_args.input_filters.exclude:
                    files.append(file)
                elif not self.app_args.input_filters.exclude.match(file.name):
                    files.append(file)

        return files

    def create_jobs(self) -> dict[Path, FFmpegJob]:
        files = self.get_files()

        jobs = dict()
        for file in files:
            info_logger.info(f'Probing file "%s"', file)
            with probe_audio_streams(file) as audio_streams:
                jobs[file] = FFmpegJob(file, audio_streams)

        return jobs


class FFmpegWorkerFactory:
    def __init__(self, app_args: AppArgs):
        self.app_args = app_args

    def create_output_filepath(self, file: Path, stream_index: int) -> Path:
        filename = Path(
            f"{file.stem}_track{stream_index}.{self.app_args.output_configuration.file_type}"
        )

        out_path = (
            self.app_args.output_dir
            if self.app_args.output_configuration.no_output_subdirs
            else self.app_args.output_dir / file.stem
        )

        out_path.mkdir(parents=True, exist_ok=True)
        return out_path / filename

    def __call__(self, job: FFmpegJob) -> FFmpegWorker:
        ffmpeg_input = ffmpeg.input(str(job.input_file))

        outputs: IndexedOutputs = dict()
        for idx, stream in enumerate(job.audio_streams):
            sample_rate = stream.get(
                "sample_rate", self.app_args.output_configuration.fallback_sample_rate
            )

            stream_index = stream["index"]
            outputs[stream_index] = ffmpeg.output(
                ffmpeg_input[f"a:{idx}"],
                str(self.create_output_filepath(job.input_file, stream_index)),
                acodec=self.app_args.output_configuration.acodec,
                audio_bitrate=sample_rate,
                overwrite_output=self.app_args.output_configuration.overwrite_existing,
            ).global_args("-progress", "-", "-nostats")

        return FFmpegWorker(job, outputs)


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


class FFmpegExtractor:
    def __init__(self, app_args: AppArgs):
        self.args = app_args
        self.job_factory = FFmpegJobFactory(app_args)
        self.worker_factory = FFmpegWorkerFactory(app_args)

    def run_synchronously(self):
        jobs = self.job_factory.create_jobs()
        workers = [self.worker_factory(job) for path, job in jobs.items()]

        progress_bars = [FFmpegProgress(worker) for worker in workers]
        group = Group(*[progress_bar.display for progress_bar in progress_bars])
        rich.print(group)

        for progress in progress_bars:
            info_logger.info("Processing input file '%s'", progress.job.input_file)
            progress.start()
            progress.run_tasks_synchronously()
