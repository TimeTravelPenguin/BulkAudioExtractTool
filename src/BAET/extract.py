import contextlib
from collections.abc import Generator, Iterator, MutableMapping
from pathlib import Path
from typing import Any

import ffmpeg  # type: ignore
from ffmpeg import Stream
from rich.console import Console, ConsoleOptions, Group, RenderResult
from rich.padding import Padding
from rich.table import Table

from ._aliases import AudioStream
from ._console import error_console
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
            raise ValueError("No audio streams found")

        logger.info("Found %d audio streams", len(audio_streams))
        yield audio_streams

    except (ffmpeg.Error, ValueError) as e:
        logger.critical("%s: %s", type(e).__name__, e)
        error_console.print_exception()
        raise e


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
        audio_streams: list[AudioStream] = []
        indexed_outputs: MutableMapping[int, Stream] = dict()

        with probe_audio_streams(file) as streams:
            for idx, stream in enumerate(streams):
                audio_streams.append(stream)

                ffmpeg_input = ffmpeg.input(str(file))
                stream_index = stream["index"]
                output_path = self._create_output_filepath(file, stream_index)
                sample_rate = stream.get(
                    "sample_rate",
                    self._output_configuration.fallback_sample_rate,
                )

                ffmpeg_output = ffmpeg.output(
                    ffmpeg_input[f"a:{idx}"],
                    str(output_path),
                    acodec=self._output_configuration.acodec,
                    audio_bitrate=sample_rate,
                )

                if self._output_configuration.overwrite_existing:
                    ffmpeg_output = ffmpeg.overwrite_output(ffmpeg_output)

                indexed_outputs[stream_index] = ffmpeg_output.global_args("-progress", "-", "-nostats")

        return FFmpegJob(file, audio_streams, indexed_outputs)

    def __iter__(self) -> Generator[FFmpegJob, Any, None]:
        yield from map(self.build_job, self._file_source_directory)


class MultiTrackAudioBulkExtractor:
    def __init__(self, app_args: AppArgs) -> None:
        self._extractor_jobs = MultitrackAudioBulkExtractorJobs(
            app_args.input_dir,
            app_args.output_dir,
            app_args.input_filters,
            app_args.output_configuration,
        )

        self.display = Table.grid()
        self._logger = logger

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield self.display

    def run_synchronously(self) -> None:
        job_progresses = [FFmpegJobProgress(job) for job in self._extractor_jobs]
        self.display.add_row(Padding(Group(*job_progresses), pad=(1, 2)))

        for progress in job_progresses:
            self._logger.info(f"Processing input file '{progress.job.input_file}'")
            progress.start()
