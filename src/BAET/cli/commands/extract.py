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

logger = create_logger()


@dataclass()
class ExtractContext:
    """Extract command context information."""

    dry_run: bool = False
    includes: list[Pattern[str]] = field(default_factory=lambda: [re.compile(".*")])
    excludes: list[Pattern[str]] = field(default_factory=lambda: [re.compile("$^")])


@dataclass()
class ExtractJob:
    def __init__(self) -> None:
        self.input: Path = Path(".")
        self.output: Path = Path(".")
        self.includes: list[Pattern[str]] = []
        self.excludes: list[Pattern[str]] = []


class ExtractJobManager:
    def __init__(self) -> None:
        self._jobs: list[ExtractJob] = []

    def get_jobs(self) -> list[ExtractJob]:
        if not self._jobs:
            return []

        merged: set[ExtractJob] = {}
        for idx, job in enumerate(self._jobs):
            others = [other.input for other_idx, other in enumerate(self._jobs) if other_idx != idx]
            if job.input in others:
                pass

    def next_job(self) -> None:
        pass


pass_extract_context = click.make_pass_decorator(ExtractContext, ensure=True)


@click.group()
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
    "--dry-run",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run without actually producing any output.",
)
@baet_config()
@pass_extract_context
def extract(ctx: ExtractContext, includes: Sequence[Pattern], excludes: Sequence[Pattern], dry_run: bool) -> None:
    """Extract click command."""
    ctx.dry_run = dry_run

    if includes:
        logger.info("Include file patterns: %s", ", ".join([f'"{p.pattern}"' for p in includes]))
    if excludes:
        logger.info("Exclude file patterns: %s", ", ".join([f'"{p.pattern}"' for p in excludes]))


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
@baet_config()
@pass_extract_context
def filter_command(ctx: ExtractContext, includes: Sequence[Pattern[str]], excludes: Sequence[Pattern[str]]) -> None:
    """Filter files for selection when providing a directory."""
    ctx.includes.extend(includes)
    ctx.excludes.extend(excludes)

    for pattern in includes:
        logger.info("Include pattern: %s", pattern)

    for pattern in excludes:
        logger.info("Exclude pattern: %s", pattern)


if __name__ == "__main__":

    class Test(Equatable):
        def __init__(self, x) -> None:
            super().__init__()
            self.x = x

        def __repr__(self) -> str:
            return self.x

    m = Merger(lambda t: t.x, lambda x, y: Test(x + y))
    x = Test("one")
    y = Test("two")
    print(x)
    print(y)
    print(m([x, y, x]))
