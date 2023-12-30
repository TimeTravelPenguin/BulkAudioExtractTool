from rich.console import Group
from rich.live import Live

from ._logging import console_logger
from .app_args import AppArgs
from .job_progress import FFmpegJobProgress
from .jobs import MultitrackAudioDirectoryExtractorJobBuilder


class FFmpegExtractor:
    def __init__(self, app_args: AppArgs):
        self.args = app_args

        job_factory = MultitrackAudioDirectoryExtractorJobBuilder(
            app_args.input_dir,
            app_args.output_dir,
            app_args.input_filters,
            app_args.output_configuration,
        )

        # TODO: This is weird
        self.jobs = list(job_factory)

    def run_synchronously(self):
        job_progresses = [FFmpegJobProgress(job) for job in self.jobs]
        group = Group(*[job_progress.display for job_progress in job_progresses])

        with Live(group):
            for progress in job_progresses:
                console_logger.info("Processing input file '%s'", progress.job.input_file)
                progress.start()