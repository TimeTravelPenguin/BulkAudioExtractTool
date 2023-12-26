from typing import TypeAlias

from ffmpeg import Stream

from Extractor import FFmpegExtractor


__all__ = ["FFmpegExtractor", "StreamIndex", "IndexedOutputs", "VIDEO_EXTENSIONS"]

VIDEO_EXTENSIONS = [".mp4", ".mkv"]
StreamIndex: TypeAlias = int
IndexedOutputs: TypeAlias = dict[StreamIndex, Stream]