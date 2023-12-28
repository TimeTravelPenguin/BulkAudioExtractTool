import contextlib
from collections.abc import Iterator
from fractions import Fraction
from pathlib import Path

import ffmpeg
from more_itertools import first_true, take

from BAET.Console import error_console
from BAET.FFmpegExtract import VIDEO_EXTENSIONS
from BAET.FFmpegExtract.Aliases import (
    AudioStream,
    IndexedAudioStream,
    IndexedOutputs,
    Millisecond,
    StreamIndex,
)
from BAET.Logging import info_logger

__all__ = ["FFmpegJobFactory", "FFmpegJob"]

from BAET.Types import InputFilters, OutputConfigurationOptions


@contextlib.contextmanager
def probe_audio_streams(file: Path) -> Iterator[list[AudioStream]]:
    try:
        info_logger.info('Probing file "%s"', file)
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
    def __init__(
        self,
        input_file: Path,
        audio_streams: list[AudioStream],
        indexed_outputs: IndexedOutputs,
    ):
        self.input_file: Path = input_file
        self.indexed_outputs: IndexedOutputs = indexed_outputs
        self.audio_streams = audio_streams
        self.indexed_audio_streams: IndexedAudioStream = dict()
        for stream in audio_streams:
            self.indexed_audio_streams[stream["index"]] = stream

        # TODO: Do we need this?
        self.durations_ms_dict: dict[StreamIndex, Millisecond] = {
            stream["index"]: self.stream_duration_ms(stream) for stream in audio_streams
        }

    @classmethod
    def stream_duration_ms(cls, stream: AudioStream) -> Millisecond:
        return (
            1_000_000
            * float(stream["duration_ts"])
            * float(Fraction(stream["time_base"]))
        )

    def stream(self, index: StreamIndex) -> AudioStream:
        stream = first_true(
            self.audio_streams,
            default=None,
            pred=lambda st: st["index"] == index,
        )

        if stream is None:
            raise IndexError(f'Stream with index "{index}" not found')

        return stream


class FFmpegJobFactory:
    def __init__(
        self,
        input_dir: Path,
        output_dir: Path,
        filters: InputFilters,
        output_configuration: OutputConfigurationOptions,
    ):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.filters = filters
        self.output_configuration = output_configuration

        self._jobs: list[FFmpegJob] = []
        self._jobs_iter: Iterator[FFmpegJob] = self.build_jobs_iter()
        self._job_count: int = 0

    def __iter__(self) -> Iterator[FFmpegJob]:
        for file in self.get_files():
            yield self.build_job(file)

    def __getitem__(self, item: int) -> FFmpegJob:
        if item < 0:
            raise IndexError("Index cannot be less than zero.")

        if item > self._job_count:
            jobs = list(take(1 + item - self._job_count, self._jobs_iter))
            self._job_count += len(jobs)

        return self._jobs[item]

    def get_files(self) -> list[Path]:
        files = []

        for file in self.input_dir.iterdir():
            if file.suffix not in VIDEO_EXTENSIONS:
                continue

            if file.is_file() and self.filters.include.match(file.name):
                if not self.filters.exclude:
                    files.append(file)
                elif not self.filters.exclude.match(file.name):
                    files.append(file)

        return files

    def create_output_filepath(self, file: Path, stream_index: int) -> Path:
        filename = Path(
            f"{file.stem}_track{stream_index}.{self.output_configuration.file_type}"
        )

        out_path = (
            self.output_dir
            if self.output_configuration.no_output_subdirs
            else self.output_dir / file.stem
        )

        out_path.mkdir(parents=True, exist_ok=True)
        return out_path / filename

    def build_job(self, file: Path) -> FFmpegJob:
        audio_streams: list[dict] = []
        indexed_outputs: IndexedOutputs = dict()

        with probe_audio_streams(file) as streams:
            for idx, stream in enumerate(streams):
                audio_streams.append(stream)

                ffmpeg_input = ffmpeg.input(str(file))
                stream_index = stream["index"]
                output_path = self.create_output_filepath(file, stream_index)
                sample_rate = stream.get(
                    "sample_rate",
                    self.output_configuration.fallback_sample_rate,
                )

                ffmpeg_output = ffmpeg.output(
                    ffmpeg_input[f"a:{idx}"],
                    str(output_path),
                    acodec=self.output_configuration.acodec,
                    audio_bitrate=sample_rate,
                )
                if self.output_configuration.overwrite_existing:
                    ffmpeg_output = ffmpeg.overwrite_output(ffmpeg_output)

                indexed_outputs[stream_index] = ffmpeg_output.global_args(
                    "-progress", "-", "-nostats"
                )

        return FFmpegJob(file, audio_streams, indexed_outputs)

    def build_jobs_iter(self) -> Iterator[FFmpegJob]:
        for file in self.get_files():
            yield self.build_job(file)
