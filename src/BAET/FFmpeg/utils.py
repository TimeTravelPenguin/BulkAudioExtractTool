"""Utilities for FFmpeg operations."""

import contextlib
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import rich_click as click

import ffmpeg
from BAET._config.console import error_console
from BAET._config.logging import create_logger
from BAET.typing import AudioStream

logger = create_logger()


@contextlib.contextmanager
def probe_file(file: Path) -> Iterator[dict[str, Any]]:
    """Probe a file using FFmpeg."""
    logger.info('Probing file "%r"', file)

    try:
        probed: dict[str, Any] = ffmpeg.probe(file)
    except ffmpeg.Error as e:
        err: str = e.stderr.decode()
        raise click.ClickException(f"Error probing file {err.strip().splitlines()[-1]}") from e

    yield probed


@contextlib.contextmanager
def probe_audio_streams(file: Path) -> Iterator[list[AudioStream]]:
    """Probe the audio streams of a file."""
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
