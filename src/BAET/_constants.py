from typing import Final, LiteralString, Sequence

type VideoExtension = Final[LiteralString]

EXT_MP4: VideoExtension = ".mp4"
EXT_MKV: VideoExtension = ".mp4"
VIDEO_EXTENSIONS: Final[Sequence[VideoExtension]] = [EXT_MP4, EXT_MKV]
