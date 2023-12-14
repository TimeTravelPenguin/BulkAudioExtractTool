from collections.abc import Mapping
from typing import Any, TypeAlias

from bidict import BidirectionalMapping
from ffmpeg import Stream
from rich.progress import TaskID

# Numbers
Millisecond: TypeAlias = int | float

# FFmpeg
StreamIndex: TypeAlias = int
AudioStream: TypeAlias = dict[str, Any]

# Mappings
IndexedOutputs: TypeAlias = Mapping[StreamIndex, Stream]
IndexedAudioStream: TypeAlias = Mapping[StreamIndex, AudioStream]
StreamTaskBiMap: TypeAlias = BidirectionalMapping[StreamIndex, TaskID]
