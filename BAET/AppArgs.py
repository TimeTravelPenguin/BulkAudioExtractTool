import argparse
from argparse import ArgumentParser
from pathlib import Path

from pydantic import DirectoryPath
from rich.console import Console, ConsoleOptions, RenderResult
from rich.markdown import Markdown
from rich.padding import Padding
from rich.rule import Rule
from rich.table import Table
from rich.text import Text
from rich_argparse import RichHelpFormatter

from BAET.Console import console
from BAET.Types import (
    AppArgs,
    AppVersion,
    DebugOptions,
    InputFilters,
    OutputConfigurationOptions,
)

APP_VERSION = AppVersion(1, 0, 0, "alpha")


class AppDescription:
    def __rich_console__(
        self, console: Console, options: ConsoleOptions
    ) -> RenderResult:
        yield Markdown("# Bulk Audio Extract Tool (BAET)")
        yield "Extract audio from a directory of videos using FFMPEG.\n"

        website_link = "https://github.com/TimeTravelPenguin/BulkAudioExtractTool"
        desc_kvps = [
            (
                Padding(Text("App name:", justify="right"), (0, 5, 0, 0)),
                Text(
                    "Bulk Audio Extract Tool (BAET)",
                    style="argparse.prog",
                    justify="left",
                ),
            ),
            (
                Padding(Text("Version:", justify="right"), (0, 5, 0, 0)),
                Text(str(APP_VERSION), style="app.version", justify="left"),
            ),
            (
                Padding(Text("Author:", justify="right"), (0, 5, 0, 0)),
                Text("Phillip Smith", style="bright_yellow", justify="left"),
            ),
            (
                Padding(Text("Website:", justify="right"), (0, 5, 0, 0)),
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
            grid.add_row(key, value)

        grid.add_row()

        yield grid
        yield Rule(Text("Commandline arguments", style="bold"), align="center")


def new_empty_argparser() -> ArgumentParser:
    def get_formatter(prog):
        return RichHelpFormatter(prog, max_help_position=35, console=console)

    # todo: use console protocol https://rich.readthedocs.io/en/stable/protocol.html#console-protocol
    description = AppDescription()

    return argparse.ArgumentParser(
        prog="Bulk Audio Extract Tool (BAET)",
        description=description,  # type: ignore
        epilog=Markdown(
            "Phillip Smith, 2023",
            justify="right",
            style="argparse.prog",
        ),  # type: ignore
        formatter_class=get_formatter,
    )


def GetArgs() -> AppArgs:
    parser = new_empty_argparser()

    parser.add_argument(
        "--version",
        action="version",
        version=f"[argparse.prog]%(prog)s[/] version [i]{APP_VERSION}[/]",
    )

    io_group = parser.add_argument_group(
        "Input/Output",
        "Options to control the source and destination directories of input and output files.",
    )

    io_group.add_argument(
        "-i",
        "--input-dir",
        default=None,
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
        help='Destination directory. Default is set to the input directory. To use the current directory, use [blue]"."[/].',
    )

    query_group = parser.add_argument_group(
        title="Input Filter Configuration",
        description="Configure how the application includes and excludes files to process.",
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
        "--output-streams-separately",
        default=False,
        action="store_true",
        help="When set, individual commands are given to [blue]ffmpeg[/] to export each stream. Otherwise, a single command is given to FFMPEG to export all streams. This latter option will result in all files appearing in the directory at once, and so any errors may result in a loss of data. Setting this flag may be useful when experiencing errors.",
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
        help="The sample rate to use if it cannot be determined via [blue]ffprobe[/].",
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
        "--logging",
        default=False,
        action="store_true",
        help="Show the logging of application execution.",
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
        default=None,
        type=int,
        dest="trim",
        help="Trim the audio to the specified number of seconds. This is useful for testing.",
    )

    args = parser.parse_args()

    if not args.output_dir:
        args.output_dir = args.input_dir

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
    )

    app_args = AppArgs.model_validate(
        {
            "input_dir": args.input_dir,
            "output_dir": args.output_dir,
            "input_filters": input_filters,
            "output_configuration": output_config,
            "debug_options": debug_options,
        }
    )

    return app_args
