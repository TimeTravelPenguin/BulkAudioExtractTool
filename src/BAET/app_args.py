import argparse
import re
from argparse import ArgumentParser
from pathlib import Path
from re import Pattern

from pydantic import BaseModel, ConfigDict, DirectoryPath, Field, field_validator
from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import Markdown
from rich.padding import Padding
from rich.table import Table
from rich.terminal_theme import DIMMED_MONOKAI
from rich.text import Text
from rich_argparse import HelpPreviewAction, RichHelpFormatter
from typing_extensions import Annotated

from ._console import app_console
from ._metadata import app_version
from ._path import ffmpeg_version_info

file_type_pattern = re.compile(r"^\.?(\w+)$")


class InputFilters(BaseModel):
    include: Pattern[str] = Field(...)
    exclude: Pattern[str] | None = Field(...)

    @field_validator("include", mode="before")
    @classmethod
    def validate_include_nonempty(cls, v: str) -> Pattern[str]:
        if v is None or not v.strip():
            return re.compile(".*")
        return re.compile(v)

    @field_validator("exclude", mode="before")
    @classmethod
    def validate_exclude_nonempty(cls, v: str) -> Pattern[str] | None:
        if v is None or not v.strip():
            return None
        return re.compile(v)


class OutputConfigurationOptions(BaseModel):
    overwrite_existing: bool = Field(...)
    no_output_subdirs: bool = Field(...)
    acodec: str = Field(...)
    fallback_sample_rate: Annotated[int, Field(gt=0)] = Field(...)
    file_type: str = Field(...)

    @field_validator("file_type", mode="before")
    @classmethod
    def validate_file_type(cls, v: str) -> str:
        matched = file_type_pattern.match(v)
        if matched:
            return matched.group(1)
        raise ValueError(f"Invalid file type: {v}")


class DebugOptions(BaseModel):
    logging: bool = Field(...)
    dry_run: bool = Field(...)
    trim: Annotated[int, Field(gt=0)] | None = Field(...)
    print_args: bool = Field(...)
    show_ffmpeg_cmd: bool = Field(...)
    run_synchronously: bool = Field(...)


class AppDescription:
    @staticmethod
    def __rich_console__(console: Console, options: ConsoleOptions) -> RenderResult:
        yield Padding(Markdown("# Bulk Audio Extract Tool"), pad=(1, 0))
        yield "Extract audio from a directory of videos using FFMPEG.\n"

        website_link = "https://github.com/TimeTravelPenguin/BulkAudioExtractTool"
        desc_kvps = [
            (
                Text("App name:", justify="right"),
                Text(
                    "Bulk Audio Extract Tool (BAET)",
                    style="argparse.prog",
                    justify="left",
                ),
            ),
            (
                Text("App Version:", justify="right"),
                Text(app_version(), style="app.version", justify="left"),
            ),
            (
                Text("FFmpeg Version:", justify="right"),
                Text(ffmpeg_version_info.version, style="app.version", justify="left"),
            ),
            (
                Text("Author:", justify="right"),
                Text("Phillip Smith", style="bright_yellow", justify="left"),
            ),
            (
                Text("Website:", justify="right"),
                Text(
                    website_link,
                    style=f"underline blue link {website_link}",
                    justify="left",
                ),
            ),
        ]

        grid = Table.grid(expand=True)
        grid.add_column(justify="left")
        grid.add_column(justify="right")
        for key, value in desc_kvps:
            grid.add_row(Padding(key, (0, 3, 0, 0)), value)

        yield grid


def new_empty_argparser() -> ArgumentParser:
    def get_formatter(prog: str) -> RichHelpFormatter:
        return RichHelpFormatter(prog, max_help_position=40, console=app_console)

    # todo: use console protocol https://rich.readthedocs.io/en/stable/protocol.html#console-protocol
    description = AppDescription()

    RichHelpFormatter.highlights.append(
        r"(?P<arg_default_parens>\((?P<arg_default>Default: (?P<arg_default_value>.*))\))"
    )

    RichHelpFormatter.highlights.append(r"(?P<help_keyword>ffmpeg|ffprobe)")
    RichHelpFormatter.highlights.append(r"(?P<debug_todo>\[TODO\])")

    return argparse.ArgumentParser(
        prog="Bulk Audio Extract Tool (src)",
        description=description,  # type: ignore
        epilog=Markdown(
            "Phillip Smith, 2024",
            justify="right",
            style="argparse.prog",
        ),
        formatter_class=get_formatter,
    )


class AppArgs(BaseModel):
    """Application commandline arguments.

    Raises:
        ValueError: The provided path is not a directory.

    Returns:
        DirectoryPath: Validated directory path.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    input_dir: DirectoryPath = Field(...)
    output_dir: DirectoryPath = Field(...)
    input_filters: InputFilters = Field(...)
    output_configuration: OutputConfigurationOptions = Field(...)
    debug_options: DebugOptions = Field(...)


def get_args() -> AppArgs:
    parser = new_empty_argparser()

    parser.add_argument(
        "--version",
        action="version",
        version=f"[argparse.prog]%(prog)s[/] version [i]{app_version()}[/]",
    )

    io_group = parser.add_argument_group(
        "Input/Output",
        "Options to control the source and destination directories of input and output files.",
    )

    io_group.add_argument(
        "-i",
        "--input-dir",
        action="store",
        type=DirectoryPath,
        metavar="INPUT_DIR",
        required=True,
        help="Source directory.",
    )

    io_group.add_argument(
        "-o",
        "--output-dir",
        default=None,
        action="store",
        type=Path,
        help="Destination directory. Default is set to the input directory. To use the current directory, "
        'use [blue]"."[/]. (Default: None)',
    )

    query_group = parser.add_argument_group(
        title="Input Filter Configuration",
        description="Configure how the application includes and excludes files to process.",
    )

    query_group.add_argument(
        "--include",
        default=None,
        metavar="REGEX",
        help='[TODO] If provided, only include files that match a regex pattern. (Default: ".*")',
    )

    query_group.add_argument(
        "--exclude",
        default=None,
        metavar="REGEX",
        help="[TODO] If provided, exclude files that match a regex pattern. (Default: None)",
    )

    output_group = parser.add_argument_group(
        title="Output Configuration",
        description="Override the default output behavior of the application.",
    )

    output_group.add_argument(
        "--overwrite-existing",
        "--overwrite",
        default=False,
        action="store_true",
        help="Overwrite a file if it already exists. (Default: False)",
    )

    output_group.add_argument(
        "--no-output-subdirs",
        default=False,
        action="store_true",
        help="Do not create subdirectories for each video's extracted audio tracks in the output directory. "
        "(Default: True)",
    )

    output_group.add_argument(
        "--acodec",
        default="pcm_s16le",
        metavar="CODEC",
        help='[TODO] The audio codec to use when extracting audio. (Default: "pcm_s16le")',
    )

    output_group.add_argument(
        "--fallback-sample-rate",
        default=48000,
        metavar="RATE",
        help="[TODO] The sample rate to use if it cannot be determined via [blue]ffprobe[/]. (Default: 48000)",
    )

    output_group.add_argument(
        "--file-type",
        default="wav",
        metavar="EXT",
        help='[TODO] The file type to use for the extracted audio. (Default: "wav")',
    )

    debug_group = parser.add_argument_group(
        "Debugging",
        "Options to help debug the application.",
    )

    debug_group.add_argument(
        "--run-synchronously",
        "--sync",
        default=False,
        action="store_true",
        help="[TODO] Run each each job in order. This should reduce the CPU workload, but may increase runtime. A "
        "'job' is per file input, regardless of whether ffmpeg commands are merged (see: "
        "`--output-streams-separately`). (Default: False)",
    )

    debug_group.add_argument(
        "--logging",
        default=False,
        action="store_true",
        help="[TODO] Show the logging of application execution. (Default: False)",
    )

    debug_group.add_argument(
        "--print-args",
        default=False,
        action="store_true",
        help="Print the parsed arguments and exit. (Default: False)",
    )

    debug_group.add_argument(
        "--dry-run",
        default=False,
        action="store_true",
        help="Run the program without actually extracting any audio. (Default: False)",
    )

    debug_group.add_argument(
        "--show-ffmpeg-cmd",
        "--cmds",
        default=False,
        action="store_true",
        help="[TODO] Print to the console the generated ffmpeg command. (Default: False)",
    )

    debug_group.add_argument(
        "--trim-short",
        default=None,
        type=int,
        dest="trim",
        help="[TODO] Trim the audio to the specified number of seconds. This is useful for testing. (Default: None)",
    )

    parser.add_argument(
        "--generate-help-preview",
        action=HelpPreviewAction,
        path="help-preview.svg",  # (optional) or "help-preview.html" or "help-preview.txt"
        export_kwds={"theme": DIMMED_MONOKAI},  # (optional) keywords passed to console.save_... methods
        help=argparse.SUPPRESS,
    )

    args = parser.parse_args()

    input_filters = InputFilters(include=args.include, exclude=args.exclude)

    output_config = OutputConfigurationOptions(
        overwrite_existing=args.overwrite_existing,
        no_output_subdirs=args.no_output_subdirs,
        acodec=args.acodec,
        fallback_sample_rate=args.fallback_sample_rate,
        file_type=args.file_type,
    )

    debug_options = DebugOptions(
        logging=args.logging,
        dry_run=args.dry_run,
        trim=args.trim,
        print_args=args.print_args,
        show_ffmpeg_cmd=args.show_ffmpeg_cmd,
        run_synchronously=args.run_synchronously,
    )

    output_dir = args.output_dir or args.input_dir
    output_dir = output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    app_args: AppArgs = AppArgs.model_validate(
        {
            "input_dir": args.input_dir.expanduser(),
            "output_dir": output_dir,
            "input_filters": input_filters,
            "output_configuration": output_config,
            "debug_options": debug_options,
        },
        strict=True,
    )

    return app_args
