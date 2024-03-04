"""Functions for validating files."""
from pathlib import Path

from BAET.constants import VIDEO_EXTENSIONS


def file_is_supported_video(file: Path) -> bool:
    """Check if the file is supported a video file.

    Parameters
    ----------
    file : Path
        The file to check.

    Returns
    -------
    bool
        True if the file is a supported video file, False otherwise.
    """
    return file.is_file() and file.suffix in VIDEO_EXTENSIONS
