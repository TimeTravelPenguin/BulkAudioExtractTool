import argparse
import re
import sys
from pathlib import Path
from re import Pattern

import rich
from pydantic import (
    BaseModel,
    ConfigDict,
    DirectoryPath,
    Field,
    FilePath,
    field_validator,
)
from rich.markdown import Markdown
from rich.text import Text
from rich_argparse import RichHelpFormatter
from typing_extensions import Annotated

from BAET.Console import console

file_type_pattern = re.compile(r"^\.?(\w+)$")


class AppArgs(BaseModel):
    """Application commandline arguments.

    Raises:
        ValueError: The provided path is not a directory.

    Returns:
        DirectoryPath: Validated directory path.
    """

    model_config = ConfigDict(frozen=True)

    input: DirectoryPath | FilePath | list[FilePath] = Field(...)
    output_dir: DirectoryPath | None = Field(...)
    overwrite_existing: bool = Field(...)
    fallback_sample_rate: Annotated[int, Field(gt=0)] = Field(...)
    trim: bool = Field(...)
    dry_run: bool = Field(...)
    output_subdirs: bool = Field(...)
    include: Pattern | None = Field(...)
    exclude: Pattern | None = Field(...)
    acodec: str = Field(...)
    file_type: str = Field(...)

    @field_validator("include", mode="before")
    @classmethod
    def validate_include_nonempty(cls, v: str):
        if not v or not str.strip(v):
            return ".*"
        return v

    @field_validator("exclude", mode="before")
    @classmethod
    def validate_exclude_nonempty(cls, v: str):
        if not v or not str.strip(v):
            return None
        return v

    @field_validator("include", "exclude", mode="before")
    @classmethod
    def compile_to_pattern(cls, v: str):
        if not v:
            return None
        if isinstance(v, str):
            return re.compile(v)
        else:
            return v

    @field_validator("file_type", mode="before")
    @classmethod
    def validate_file_type(cls, v: str):
        matched = file_type_pattern.match(v)
        if matched:
            return matched.group(1)
        raise ValueError(f"Invalid file type: {v}")


def GetArgs() -> AppArgs:
    def get_formatter(prog):
        return RichHelpFormatter(prog, max_help_position=35, console=console)

    # todo: use console protocol https://rich.readthedocs.io/en/stable/protocol.html#console-protocol
    description = Markdown(
        """
# Bulk Audio Extract Tool (BAET)

Extract audio from a directory of videos using FFMPEG.

### Website: [https://github.com/TimeTravelPenguin/BulkAudioExtractTool](https://github.com/TimeTravelPenguin/BulkAudioExtractTool)
""",
    )

    parser = argparse.ArgumentParser(
        prog="Bulk Audio Extract Tool (BAET)",
        description=description,  # type: ignore
        epilog=Markdown(
            "Author: Phillip Smith, 2023",
            justify="right",
            style="argparse.prog",
        ),  # type: ignore
        formatter_class=get_formatter,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="[argparse.prog]%(prog)s[/] version [i]1.0.0[/]",
    )

    io_group = parser.add_argument_group(
        "Input/Output",
        "Options to control the source and destination directories of input and output files.",
    )

    input_group = io_group.add_mutually_exclusive_group(required=True)

    input_group.add_argument(
        "-i",
        "--input-dir",
        default=None,
        action="store",
        dest="input",
        type=Path,
        metavar="INPUT_DIR",
        help="Source directory.",
    )

    input_group.add_argument(
        "-f",
        "--input-file",
        default=None,
        action="append",
        dest="input",
        type=Path,
        metavar="FILE",
        help="Add a source file.",
    )

    io_group.add_argument(
        "-o",
        "--output-dir",
        default=None,
        type=Path,
        help="Destination directory. Default is set to the input directory. To use the current directory, use [green]'.'[/green]",
    )

    query_group = parser.add_argument_group(
        title="Query Configuration",
        description="Configure how the application selects files to process.",
    )

    query_group.add_argument(
        "--include",
        default=None,
        metavar="REGEX",
        help="If provided, only include files that match a regex pattern.",
    )

    query_group.add_argument(
        "--exclude",
        default=None,
        metavar="REGEX",
        help="If provided, exclude files that match a regex pattern.",
    )

    output_group = parser.add_argument_group(
        title="Output Configuration",
        description="Override the default output behavior of the application.",
    )

    output_group.add_argument(
        "--overwrite-existing",
        default=False,
        action="store_true",
        help="Overwrite a file if it already exists.",
    )

    output_group.add_argument(
        "--no-output-subdirs",
        default=True,
        action="store_true",
        help="Do not create subdirectories for each video's extracted audio tracks in the output directory.",
    )

    output_group.add_argument(
        "--acodec",
        default="pcm_s16le",
        metavar="CODEC",
        help="The audio codec to use when extracting audio.",
    )

    output_group.add_argument(
        "--fallback-sample-rate",
        default=48000,
        metavar="RATE",
        help="The sample rate to use if it cannot be determined via [blue]ffprobe[/blue].",
    )

    output_group.add_argument(
        "--file-type",
        default="wav",
        metavar="EXT",
        help="The file type to use for the extracted audio.",
    )

    debug_group = parser.add_argument_group(
        "Debugging",
        "Options to help debug the application.",
    )

    debug_group.add_argument(
        "--print-args",
        default=False,
        action="store_true",
        help="Print the parsed arguments and exit.",
    )

    debug_group.add_argument(
        "--dry-run",
        default=False,
        action="store_true",
        help="Run the program without actually extracting any audio.",
    )

    debug_group.add_argument(
        "--trim-short",
        default=10,
        help="Trim the audio to the specified number of seconds. This is useful for testing.",
    )

    args = parser.parse_args()

    if args.print_args:
        rich.print(vars(args))
        sys.exit(0)

    return AppArgs.model_validate(vars(args), strict=False)
