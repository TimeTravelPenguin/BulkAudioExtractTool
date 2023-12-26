from pathlib import Path

import ffmpeg
import rich
from rich.console import Group

from BAET.AppArgs import AppArgs
from BAET.FFmpegExtract import IndexedOutputs
from BAET.FFmpegExtract.Job import FFmpegJob, FFmpegJobFactory
from BAET.FFmpegExtract.Progress import FFmpegProgress
from BAET.Logging import info_logger


__all__ = ["FFmpegExtractor", "FFmpegWorker", "FFmpegWorkerFactory"]


class FFmpegWorker:
    def __init__(self, job: FFmpegJob, indexed_outputs: IndexedOutputs):
        self.job = job
        self.indexed_outputs: IndexedOutputs = indexed_outputs


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