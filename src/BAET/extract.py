from rich.console import Group
from rich.live import Live

from BAET.app_args import AppArgs
from BAET.jobs import FFmpegJobFactory


__all__ = ["FFmpegExtractor"]

from BAET.job_progress import FFmpegJobProgress


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
        job_progresses = [FFmpegJobProgress(job) for job in self.jobs]
        group = Group(*[job_progress.display for job_progress in job_progresses])

        with Live(group):
            for progress in job_progresses:
                # info_logger.info("Processing input file '%s'", progress.job.input_file)
                progress.start()
