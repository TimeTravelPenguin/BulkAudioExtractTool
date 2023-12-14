import argparse
import re
from pathlib import Path
from re import Pattern
from typing import Any, Callable, cast

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    DirectoryPath,
    Field,
    ValidationInfo,
    field_validator,
)
from typing_extensions import Annotated


class AppArgs(BaseModel):
    """Application commandline arguments.

    Raises:
        ValueError: The provided path is not a directory.

    Returns:
        DirectoryPath: Validated directory path.
    """

    model_config = ConfigDict(frozen=True)

    input_dir: DirectoryPath = Field(...)
    output_dir: DirectoryPath = Field(...)
    overwrite_existing: bool = Field(...)
    fallback_freq: Annotated[int, Field(gt=0)] = Field(...)
    fast: bool = Field(...)
    no_output_subdirs: bool = Field(...)
    include: Pattern | None = Field(...)
    exclude: Pattern | None = Field(...)

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


def GetArgs() -> AppArgs:
    cwd = str(Path.cwd())

    parser = argparse.ArgumentParser(
        prog="Bulk Audio Extract Tool (BAET)",
        description="Extract audio from a directory of videos using FFMPEG",
        epilog="Created by: Phillip Smith 2023",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--fast",
        default=False,
        action="store_true",
        help="only extracting the first 10 seconds of audio for each file",
    )

    parser.add_argument(
        "--overwrite-existing",
        default=False,
        action="store_true",
        help="overwrite a file if it already exists",
    )

    parser.add_argument(
        "--no-output-subdirs",
        default=False,
        action="store_true",
        help="do not create subdirectories for each video's extracted audio tracks in the output directory",
    )

    parser.add_argument(
        "--include",
        default=None,
        metavar="REGEX",
        help="only include files that match a regex pattern",
    )

    parser.add_argument(
        "--exclude",
        default=None,
        metavar="REGEX",
        help="exclude files that match a regex pattern",
    )

    parser.add_argument(
        "--fallback-freq",
        default=48000,
        metavar="FREQUENCY",
        help="------------------",
    )

    parser.add_argument(
        "-i", "--input-dir", default=cwd, type=Path, help="source location"
    )
    parser.add_argument(
        "-o", "--output-dir", default=cwd, type=Path, help="destination location"
    )

    args = parser.parse_args()
    return AppArgs.model_validate(vars(args))
