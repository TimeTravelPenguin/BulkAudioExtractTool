import contextlib
from collections.abc import Generator, Iterator
from fractions import Fraction
from pathlib import Path

import ffmpeg
from more_itertools import first_true

from ._aliases import (
    AudioStream,
    IndexedAudioStream,
    IndexedOutputs,
    Millisecond,
    StreamIndex,
)
from ._console import error_console
from ._constants import VIDEO_EXTENSIONS
from ._logging import console_logger
from .app_args import InputFilters, OutputConfigurationOptions


@contextlib.contextmanager
def probe_audio_streams(file: Path) -> Iterator[list[AudioStream]]:
    try:
        console_logger.info('Probing file "%s"', file)
        probe = ffmpeg.probe(file)

        audio_streams = sorted(
            [stream for stream in probe["streams"] if "codec_type" in stream and stream["codec_type"] == "audio"],
            key=lambda stream: stream["index"],
        )

        if not audio_streams:
            raise ValueError("No audio streams found")

        console_logger.info("Found %d audio streams", len(audio_streams))
        yield audio_streams

    except (ffmpeg.Error, ValueError) as e:
        console_logger.critical("%s: %s", type(e).__name__, e)
        error_console.print_exception()
        raise e


class FFmpegJob:
    def __init__(
        self,
        input_file: Path,
        audio_streams: list[AudioStream],
        indexed_outputs: IndexedOutputs,
    ):
        self.input_file: Path = input_file
        self.indexed_outputs: IndexedOutputs = indexed_outputs
        self.audio_streams = audio_streams

        indexed_audio_streams = dict()
        for stream in audio_streams:
            indexed_audio_streams[stream["index"]] = stream
        self.indexed_audio_streams: IndexedAudioStream = indexed_audio_streams

        # TODO: Do we need this?
        self.durations_ms_dict: dict[StreamIndex, Millisecond] = {
            stream["index"]: self.stream_duration_ms(stream) for stream in audio_streams
        }

    @classmethod
    def stream_duration_ms(cls, stream: AudioStream) -> Millisecond:
        return 1_000_000 * float(stream["duration_ts"]) * float(Fraction(stream["time_base"]))

    def stream(self, index: StreamIndex) -> AudioStream:
        stream = first_true(
            self.audio_streams,
            default=None,
            pred=lambda st: st["index"] == index,
        )

        if stream is None:
            raise IndexError(f'Stream with index "{index}" not found')

        return stream


class FileSourceDirectory:
    def __init__(self, directory: Path, filters: InputFilters):
        if not directory.is_dir():
            raise NotADirectoryError(directory)  # FIXME: Is this right?

        self._directory = directory.resolve(strict=True)
        self._filters = filters

    def __iter__(self) -> Generator[Path]:
        for file in self._directory.iterdir():
            if not file.is_file():
                continue

            # TODO: This should be moved. Rather than checking a global variable, it should
            #   be provided somehow. Perhaps via command line args.
            if file.suffix not in VIDEO_EXTENSIONS:
                continue

            if self._filters.include.match(file.name):
                if self._filters.exclude is not None and not self._filters.exclude.match(file.name):
                    yield file


class MultitrackAudioDirectoryExtractorJobBuilder:
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

    def create_output_filepath(self, file: Path, stream_index: int) -> Path:
        filename = Path(f"{file.stem}_track{stream_index}.{self._output_configuration.file_type}")

        out_path = self._output_dir if self._output_configuration.no_output_subdirs else self._output_dir / file.stem

        out_path.mkdir(parents=True, exist_ok=True)
        return out_path / filename

    def build_job(self, file: Path) -> FFmpegJob:
        audio_streams: list[dict] = []
        indexed_outputs = dict()

        with probe_audio_streams(file) as streams:
            for idx, stream in enumerate(streams):
                audio_streams.append(stream)

                ffmpeg_input = ffmpeg.input(str(file))
                stream_index = stream["index"]
                output_path = self.create_output_filepath(file, stream_index)
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

    def __iter__(self) -> Generator[FFmpegJob]:
        yield from map(self.build_job, self._file_source_directory)