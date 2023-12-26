import contextlib
from fractions import Fraction
from pathlib import Path
from typing import Iterator

import ffmpeg

from BAET.Console import error_console
from BAET.FFmpegExtract import VIDEO_EXTENSIONS
from BAET.Logging import info_logger
from BAET.Types import AppArgs


__all__ = ["FFmpegJobFactory", "FFmpegJob"]


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