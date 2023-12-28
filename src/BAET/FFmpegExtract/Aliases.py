from collections.abc import MutableMapping

from ffmpeg import Stream

type Millisecond = int | float

type StreamIndex = int
type IndexedOutputs = MutableMapping[StreamIndex, Stream]
type AudioStream = dict
type IndexedAudioStream = MutableMapping[StreamIndex, AudioStream]
