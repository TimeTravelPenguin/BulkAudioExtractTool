"""Constants for BAET."""

import typing
from collections.abc import Sequence
from typing import Final, Literal

# TODO: Refactor required
VideoExtension = Literal[".mp4", ".mkv", ".avi", ".webm"]
VideoExtension_NoDot = Literal["mp4", "mkv", "avi", "webm"]

# TODO: Refactor required
VIDEO_EXTENSIONS: Final[Sequence[VideoExtension]] = [".mp4", ".mkv", ".avi", ".webm"]
VIDEO_EXTENSIONS_NO_DOT: Final[tuple[VideoExtension_NoDot, ...]] = typing.get_args(VideoExtension_NoDot)

AudioExtension = Literal["mp3", "wav", "flac", "ogg"]
AUDIO_EXTENSIONS: Final[tuple[AudioExtension, ...]] = typing.get_args(AudioExtension)
