"""Constants for BAET."""

from collections.abc import Set
from typing import Literal, TypeAlias

VideoExtension: TypeAlias = Literal[".mp4", ".mkv", ".avi", ".webm"]

VIDEO_EXTENSIONS: Set[str] = {".mp4", ".mkv", ".avi", ".webm"}
