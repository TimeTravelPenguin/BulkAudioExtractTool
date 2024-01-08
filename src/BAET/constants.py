from collections.abc import Sequence
from typing import Literal, TypeAlias

# TODO: Remove dots from extensions
VideoExtension: TypeAlias = Literal[".mp4", ".mkv", ".avi", ".webm"]

VIDEO_EXTENSIONS: Sequence[VideoExtension] = [".mp4", ".mkv", ".avi", ".webm"]
