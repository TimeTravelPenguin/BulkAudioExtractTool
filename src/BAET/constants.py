from collections.abc import Sequence
"""Constants for BAET."""
from typing import Literal, TypeAlias

VideoExtension: TypeAlias = Literal[".mp4", ".mkv", ".avi", ".webm"]

VIDEO_EXTENSIONS: Sequence[VideoExtension] = [".mp4", ".mkv", ".avi", ".webm"]
