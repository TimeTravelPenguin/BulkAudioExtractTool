import sys
from pathlib import Path

import ffmpeg
from pydantic import DirectoryPath, FilePath
from rich import print as pprint
from rich.traceback import install

from BAET.AppArgs import GetArgs
from BAET.AudioExtractor import AudioExtractor

install(show_locals=True)

VIDEO_EXTENSIONS = [".mp4", ".mkv"]


def get_files_in_dir(dir_path: Path) -> list[Path]:
    """Get all files in a directory with the specified extension.

    Args:
        dir_path (DirectoryPath | FilePath | list[FilePath]): Path to the directory, file, or list of files.
        extension (str): File extension to filter by when given a directory path.

    Returns:
        list[Path]: List of files in the directory with the specified extension.
    """

    return [file for file in dir_path.iterdir() if file.suffix in VIDEO_EXTENSIONS]


def main():
    args = GetArgs()

    if isinstance(args.input, Path) and args.input.is_dir():
        files = get_files_in_dir(args.input)
    elif isinstance(args.input, list):
        files = args.input
    else:
        raise ValueError("Input must be a directory or list of files.")

    for file in files:
        ex = AudioExtractor(file, args)
        ex.extract()


if __name__ == "__main__":
    main()
