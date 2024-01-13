from pathlib import Path

from BAET.constants import VIDEO_EXTENSIONS


def file_is_video(file: Path) -> bool:
    return file.is_file() and file.suffix in VIDEO_EXTENSIONS
