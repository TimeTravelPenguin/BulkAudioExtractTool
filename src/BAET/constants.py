"""Constants for BAET."""

from collections.abc import Sequence
from typing import Final, Literal

# TODO: Refactor required
type VideoExtension = Literal[".mp4", ".mkv", ".avi", ".webm"]
type VideoExtension_NoDot = Literal["mp4", "mkv", "avi", "webm"]

# TODO: Refactor required
VIDEO_EXTENSIONS: Final[Sequence[VideoExtension]] = [".mp4", ".mkv", ".avi", ".webm"]
VIDEO_EXTENSIONS_NO_DOT: Final[Sequence[VideoExtension_NoDot]] = ["mp4", "mkv", "avi", "webm"]

type AudioExtensions = Literal["mp3", "wav", "flac", "ogg"]
AUDIO_EXTENSIONS: Final[Sequence[AudioExtensions]] = ["mp3", "wav", "flac", "ogg"]
