from fractions import Fraction
from pathlib import Path

from more_itertools import first_true

from ._aliases import AudioStream, IndexedAudioStream, IndexedOutputs, Millisecond, StreamIndex


class FFmpegJob:
    def __init__(
        self,
        input_file: Path,
        audio_streams: list[AudioStream],
        indexed_outputs: IndexedOutputs,
    ):
        self.input_file: Path = input_file
        self.indexed_outputs: IndexedOutputs = indexed_outputs
        self.audio_streams = audio_streams

        indexed_audio_streams = {}
        for stream in audio_streams:
            indexed_audio_streams[stream["index"]] = stream
        self.indexed_audio_streams: IndexedAudioStream = indexed_audio_streams

        # TODO: Do we need this?
        self.durations_ms_dict: dict[StreamIndex, Millisecond] = {
            stream["index"]: self.stream_duration_ms(stream) for stream in audio_streams
        }

    @classmethod
    def stream_duration_ms(cls, stream: AudioStream) -> Millisecond:
        return 1_000_000 * float(stream["duration_ts"]) * float(Fraction(stream["time_base"]))

    def stream(self, index: StreamIndex) -> AudioStream:
        stream: AudioStream | None = first_true(
            self.audio_streams,
            default=None,
            pred=lambda st: st["index"] == index,
        )

        if stream is None:
            raise IndexError(f'Stream with index "{index}" not found')

        return stream
