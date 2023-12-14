import contextlib
from collections.abc import Generator, Iterator, MutableMapping
from pathlib import Path
from typing import Any

import ffmpeg
from ffmpeg import Stream
from rich.console import Console, ConsoleOptions, Group, RenderResult
from rich.padding import Padding
from rich.prompt import Confirm
from rich.table import Table

from ._aliases import AudioStream
from ._console import app_console, error_console
from ._constants import VIDEO_EXTENSIONS
from ._logging import create_logger
from .app_args import AppArgs, InputFilters, OutputConfigurationOptions
from .job_progress import FFmpegJobProgress
from .jobs import FFmpegJob

logger = create_logger()


@contextlib.contextmanager
def probe_audio_streams(file: Path) -> Iterator[list[AudioStream]]:
    try:
        logger.info('Probing file "%s"', file)
        probe = ffmpeg.probe(file)

        audio_streams = sorted(
            [stream for stream in probe["streams"] if "codec_type" in stream and stream["codec_type"] == "audio"],
            key=lambda stream: stream["index"],
        )

        if not audio_streams:
            logger.warning("No audio streams found")
            yield []
            return

        logger.info("Found %d audio streams", len(audio_streams))
        yield audio_streams

    except (ffmpeg.Error, ValueError) as e:
        logger.critical("%s: %s", type(e).__name__, e)
        error_console.print_exception()
        raise e


def can_write_file(file: Path, has_overwrite_permission: bool) -> bool:
    if not file.exists():
        return True

    if has_overwrite_permission:
        return True

    return Confirm.ask(  # type: ignore
        f'The file "{file.name}" already exists. Overwrite?',
        console=app_console,
    )


class FileSourceDirectory:
    def __init__(self, directory: Path, filters: InputFilters):
        if not directory.is_dir():
            raise NotADirectoryError(directory)  # FIXME: Is this right?

        self._directory = directory.resolve(strict=True)
        self._filters = filters

    def __iter__(self) -> Generator[Path, Any, None]:
        for file in self._directory.iterdir():
            if not file.is_file():
                continue

            # TODO: This should be moved.
            #  Rather than checking a global variable, it should be provided somehow.
            #  Perhaps via command line args.
            if file.suffix not in VIDEO_EXTENSIONS:
                continue

            if self._filters.include.match(file.name):
                if self._filters.exclude is None:
                    yield file
                elif self._filters.exclude.match(file.name):
                    yield file


class MultitrackAudioBulkExtractorJobs:
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        filters: InputFilters,
        output_configuration: OutputConfigurationOptions,
    ):
        self._input_dir = input_dir
        self._output_dir = output_dir
        self._filters = filters
        self._output_configuration = output_configuration
        self._file_source_directory = FileSourceDirectory(input_dir, filters)

    def _create_output_filepath(self, file: Path, stream_index: int) -> Path:
        filename = Path(f"{file.stem}_track{stream_index}.{self._output_configuration.file_type}")

        out_path = self._output_dir if self._output_configuration.no_output_subdirs else self._output_dir / file.stem

        out_path.mkdir(parents=True, exist_ok=True)
        return out_path / filename

    def build_job(self, file: Path) -> FFmpegJob:
        logger.info(f'Building job for "{file}"')

        audio_streams: list[AudioStream] = []
        indexed_outputs: MutableMapping[int, Stream] = {}

        file = file.expanduser()
        with probe_audio_streams(file) as streams:
            for idx, stream in enumerate(streams):
                ffmpeg_input = ffmpeg.input(str(file))
                stream_index = stream["index"]
                output_path = self._create_output_filepath(file, stream_index)
                sample_rate = stream.get(
                    "sample_rate",
                    self._output_configuration.fallback_sample_rate,
                )

                can_write = can_write_file(
                    file=output_path,
                    has_overwrite_permission=self._output_configuration.overwrite_existing,
                )

                if can_write:
                    # Add stream here since otherwise there will possibly be more streams to indexes
                    # TODO: Maybe make a function/class to help with this?
                    audio_streams.append(stream)

                    indexed_outputs[stream_index] = (
                        ffmpeg.output(
                            ffmpeg_input[f"a:{idx}"],
                            str(output_path),
                            acodec=self._output_configuration.acodec,
                            audio_bitrate=sample_rate,
                        )
                        .overwrite_output()
                        .global_args("-progress", "-", "-nostats")
                    )

        return FFmpegJob(file, audio_streams, indexed_outputs)

    def __iter__(self) -> Generator[FFmpegJob, Any, None]:
        yield from map(self.build_job, self._file_source_directory)


class MultiTrackAudioBulkExtractor:
    def __init__(self, app_args: AppArgs) -> None:
        logger.info("Starting MultiTrackAudioBulkExtractor")

        self._app_args = app_args
        self._extractor_jobs = MultitrackAudioBulkExtractorJobs(
            app_args.input_dir,
            app_args.output_dir,
            app_args.input_filters,
            app_args.output_configuration,
        )

        # Need to compile the jobs here, otherwise rich bugs out when prompting.
        # This is because run_synchronously is called within a live display, which is buggy.
        # In the future, a refactor to separate the running of jobs from this class can make things less complex
        self._jobs = list(self._extractor_jobs)

        self.display = Table.grid()

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield self.display

    def run_synchronously(self) -> None:
        job_progresses = [FFmpegJobProgress(job) for job in self._jobs]
        self.display.add_row(Padding(Group(*job_progresses), pad=(1, 2)))

        logger.info("Starting synchronous execution of queued jobs")
        for progress in job_progresses:
            logger.info(f'Starting job "{progress.job.input_file}"')
            progress.start()
