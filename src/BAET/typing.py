"""Typing definitions for BAET."""

from collections.abc import Mapping
from typing import Any

from bidict import BidirectionalMapping
from rich.progress import TaskID

from ffmpeg import Stream

# Numbers
type Millisecond = int | float

# FFmpeg
type StreamIndex = int
type AudioStream = dict[str, Any]
type FFmpegOutput = Stream

# Mappings
type IndexedOutputs = Mapping[StreamIndex, FFmpegOutput]
type IndexedAudioStream = Mapping[StreamIndex, AudioStream]
type StreamTaskBiMap = BidirectionalMapping[StreamIndex, TaskID]
