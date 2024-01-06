from collections.abc import Sequence
from typing import Literal, TypeAlias

VideoExtension: TypeAlias = Literal[".mp4", ".mkv"]

VIDEO_EXTENSIONS: Sequence[VideoExtension] = [".mp4", ".mkv"]
