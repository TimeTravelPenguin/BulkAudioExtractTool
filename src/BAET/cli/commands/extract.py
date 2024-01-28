"""Extract click command."""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from re import Pattern

import rich_click as click

from BAET._config.logging import create_logger
from BAET.cli.help_configuration import baet_config
from BAET.cli.types import RegexPattern
from BAET.constants import VIDEO_EXTENSIONS, VideoExtension

logger = create_logger()


@dataclass()
class ExtractContext:
    """Extract command context information."""

    dry_run: bool = False
    includes: list[Pattern[str]] = field(default_factory=lambda: [re.compile(".*")])
    excludes: list[Pattern[str]] = field(default_factory=lambda: [re.compile("$^")])


@dataclass(frozen=True)
class ExtractJob:
    input_outputs: list[tuple[Path, Path]] = field(default_factory=lambda: [], hash=True)
    includes: list[Pattern[str]] = field(default_factory=lambda: [], hash=True)
    excludes: list[Pattern[str]] = field(default_factory=lambda: [], hash=True)


pass_extract_context = click.make_pass_decorator(ExtractJob, ensure=True)


@click.group(chain=True, invoke_without_command=True)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run without actually producing any output.",
)
@baet_config()
@pass_extract_context
def extract(ctx: ExtractJob, dry_run: bool) -> None:
    """Extract click command."""
    pass


@extract.result_callback()
@pass_extract_context
def process(ctx: ExtractJob, dry_run: bool):
    pass


@extract.command("file")
@click.option(
    "--input",
    "-i",
    "input_",
    help="The file to extract audio from.",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True, path_type=Path),
    required=True,
)
@click.option(
    "--output",
    "-o",
    help="The output file or directory to output to.",
    type=click.Path(exists=False, resolve_path=True, path_type=Path),
)
@baet_config()
def input_file(input_: Path, output: Path) -> None:
    """Extract specific tracks from a video file."""
    logger.info("Extracting audio tracks from video file: %s", input_)
    logger.info("Extracting to: %s", output)


@extract.command("dir")
@click.option(
    "--input",
    "-i",
    "input_",
    help="The directory of videos to extract audio from.",
    type=click.Path(exists=True, file_okay=False, resolve_path=True, path_type=Path),
    required=True,
)
@click.option(
    "--output",
    "-o",
    help="The output directory.",
    default=Path("./outputs"),
    show_default="./outputs",
    type=click.Path(exists=False, file_okay=False, resolve_path=True, path_type=Path),
)
@baet_config()
def input_dir(input_: Path, output: Path) -> None:
    """Extract specific tracks from a video file."""
    logger.info("Extracting audio tracks from video in dir: %s", input_)
    logger.info("Extracting to directory: %s", output)

    files = [str(f) for f in input_.iterdir() if f.is_file()]
    logger.info("Directory files: %s", ", ".join(files))


@extract.command("filter")
@click.option(
    "--include",
    "includes",
    multiple=True,
    type=RegexPattern,
    show_default=".*",
    default=[".*"],
    help="Include files matching this pattern.",
)
@click.option(
    "--exclude",
    "excludes",
    multiple=True,
    type=RegexPattern,
    show_default="$^",
    default=["$^"],
    help="Include files matching this pattern.",
)
@click.option(
    "--ext",
    "extensions",
    help="Specify which video extensions to include in the directory.",
    type=click.Choice(VIDEO_EXTENSIONS),
    default=VIDEO_EXTENSIONS,
)
@baet_config()
@pass_extract_context
def filter_command(
    ctx: ExtractContext,
    includes: Sequence[Pattern[str]],
    excludes: Sequence[Pattern[str]],
    extensions: Sequence[VideoExtension],
) -> None:
    """Filter files for selection when providing a directory."""
    # for extension in extensions:
    #     ctx.includes.append(re.compile(f".*{extension}$"))
    ctx.includes.append(re.compile(f".*({"|".join(extensions)})"))
    ctx.includes.extend(includes)
    ctx.excludes.extend(excludes)

    if includes:
        logger.info("Include file patterns: %s", ", ".join([f'"{p.pattern}"' for p in includes]))
    if excludes:
        logger.info("Exclude file patterns: %s", ", ".join([f'"{p.pattern}"' for p in excludes]))
