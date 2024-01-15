"""Jobs that encapsulate work to be done by FFmpeg."""

from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import overload

import rich.repr
from more_itertools import first_true

from ..typing import AudioStream, FFmpegOutput, IndexedAudioStream, IndexedOutputs, Millisecond, StreamIndex


@rich.repr.auto()
class JobMetadata:
    """Metadata for an FFmpeg job."""

    @overload
    def __init__(
        self,
        input_file: Path,
        output_dir: Path,
        *,
        audio_stream_indexes: Sequence[StreamIndex],
        job_outputs: Sequence[FFmpegOutput],
    ):
        ...

    @overload
    def __init__(
        self,
        input_file: Path,
        output_dir: Path,
        *,
        stream_indexed_output_map: IndexedOutputs,
    ):
        ...

    def __init__(
        self,
        input_file: Path,
        output_dir: Path,
        *,
        audio_stream_indexes: Sequence[StreamIndex] | None = None,
        job_outputs: Sequence[FFmpegOutput] | None = None,
        stream_indexed_output_map: IndexedOutputs | None = None,
    ):
        """
        Metadata for an FFmpeg job.

        Parameters
        ----------
        input_file : Path
            The input file path
        output_dir : Path
            The output directory path
        audio_stream_indexes : Sequence[StreamIndex] | None, optional
            The audio stream indexes to extract, by default None
        job_outputs : Sequence[FFmpegOutput] | None, optional
            The FFmpeg outputs for the job, by default None
        stream_indexed_output_map : IndexedOutputs | None, optional
            The map of stream indexes to FFmpeg outputs, by default None

        Raises
        ------
        ValueError
            Either `audio_stream_indexes` and `job_outputs` or `stream_indexed_output_map` must be provided

        Notes
        -----
        - If `audio_stream_indexes` and `job_outputs` are provided, they will be used to initialize the job metadata.
        - If `stream_indexed_output_map` is provided, it will be used to initialize the job metadata.
        - If both `audio_stream_indexes` and `stream_indexed_output_map` are provided,
            `audio_stream_indexes` will take precedence.
        """
        self.input_file = input_file
        self.output_dir = output_dir

        self.audio_stream_indexes = audio_stream_indexes
        self.job_outputs = job_outputs

        self.stream_indexed_output_map = stream_indexed_output_map

        if self.stream_indexed_output_map is not None:
            self.audio_stream_indexes, self.job_outputs = zip(*self.stream_indexed_output_map.items())
            return

        if self.audio_stream_indexes is None or self.job_outputs is None:
            raise ValueError(
                "Either `audio_stream_indexes` and `job_outputs` or `stream_indexed_output_map` must be provided"
            )

        self.stream_indexed_output_map = dict(zip(self.audio_stream_indexes, self.job_outputs))


class AudioExtractJob:
    def __init__(
        self,
        input_file: Path,
        audio_streams: list[AudioStream],
        indexed_outputs: IndexedOutputs,
    ):
        self.input_file: Path = input_file
        self.stream_indexed_outputs: IndexedOutputs = indexed_outputs
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
            pred=lambda st: st["index"] == index if st is not None else None,
        )

        if stream is None:
            raise IndexError(f'Stream with index "{index}" not found')

        return stream


if __name__ == "__main__":
    meta = JobMetadata(
        input_file=Path("in"),
        output_dir=Path("out"),
        stream_indexed_output_map={x: f"Job {x:02d}" for x in range(1, 5)},
    )

    rich.print(meta)