from typing import TypeAlias

from ffmpeg import Stream


StreamIndex: TypeAlias = int
IndexedOutputs: TypeAlias = dict[StreamIndex, Stream]