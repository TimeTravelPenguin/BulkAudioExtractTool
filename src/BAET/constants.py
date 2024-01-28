"""Constants for BAET."""

from collections.abc import Sequence
from typing import Literal

type VideoExtension = Literal[".mp4", ".mkv", ".avi", ".webm"]

VIDEO_EXTENSIONS: Sequence[VideoExtension] = [".mp4", ".mkv", ".avi", ".webm"]
