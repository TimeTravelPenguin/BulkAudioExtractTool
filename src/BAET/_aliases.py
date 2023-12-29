from collections.abc import Mapping

from bidict import BidirectionalMapping
from ffmpeg import Stream
from rich.progress import TaskID


# Numbers
type Millisecond = int | float

# FFmpeg
type StreamIndex = int
type AudioStream = dict

# Mappings
type IndexedOutputs = Mapping[StreamIndex, Stream]
type IndexedAudioStream = Mapping[StreamIndex, AudioStream]
type StreamTaskBiMap = BidirectionalMapping[StreamIndex, TaskID]