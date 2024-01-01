from collections.abc import Mapping
from typing import Any

from bidict import BidirectionalMapping
from ffmpeg import Stream  # type: ignore
from rich.progress import TaskID

# Numbers
type Millisecond = int | float

# FFmpeg
type StreamIndex = int
type AudioStream = dict[str, Any]

# Mappings
type IndexedOutputs = Mapping[StreamIndex, Stream]
type IndexedAudioStream = Mapping[StreamIndex, AudioStream]
type StreamTaskBiMap = BidirectionalMapping[StreamIndex, TaskID]
