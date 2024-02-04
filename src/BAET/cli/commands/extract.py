"""Extract click command."""

import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from re import Pattern
from typing import Concatenate

import rich_click as click
from rich import print

from BAET._config.logging import create_logger
from BAET.cli.help_configuration import baet_config
from BAET.cli.types import RegexPattern
from BAET.constants import VIDEO_EXTENSIONS_NO_DOT, VideoExtension_NoDot

logger = create_logger()


@dataclass()
class ExtractJob:
    input_outputs: list[tuple[Path, Path]] = field(default_factory=lambda: [])
    includes: list[Pattern[str]] = field(default_factory=lambda: [])
    excludes: list[Pattern[str]] = field(default_factory=lambda: [])


pass_extract_context = click.make_pass_decorator(ExtractJob, ensure=True)

type ExtractJobProcessor[**P] = Callable[P, Callable[[ExtractJob], ExtractJob]]


def processor[**P](
    f: Callable[Concatenate[ExtractJob, P], ExtractJob],
) -> ExtractJobProcessor[P]:
    """Produce an `ExtractJob`-accepting function from a function that accepts multiple arguments."""

    @wraps(f)
    def new_func(*args: P.args, **kwargs: P.kwargs) -> Callable[[ExtractJob], ExtractJob]:
        def _processor(job: ExtractJob) -> ExtractJob:
            return f(job, *args, **kwargs)

        return _processor

    return new_func


@click.group(chain=True, invoke_without_command=True)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run without actually producing any output.",
)
@baet_config()
def extract(dry_run: bool) -> None:
    """Extract click command."""
    pass


@extract.result_callback()
def process(processors: Sequence[Callable[[ExtractJob], ExtractJob]], dry_run: bool) -> None:
    logger.info("Dry run: %s", dry_run)

    job = ExtractJob()
    for p in processors:
        job = p(job)

    for include in job.includes:
        job.input_outputs = list(filter(lambda x: include.match(x[0].name), job.input_outputs))

    for exclude in job.excludes:
        job.input_outputs = list(filter(lambda x: not exclude.match(x[0].name), job.input_outputs))

    print(job)


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
@processor
def input_file(job: ExtractJob, input_: Path, output: Path) -> ExtractJob:
    """Extract specific tracks from a video file."""
    logger.info("Extracting audio tracks from video file: %s", input_)
    logger.info("Extracting to: %s", output)

    job.input_outputs.append((input_, output))
    return job


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
@processor
def input_dir(job: ExtractJob, input_: Path, output: Path) -> ExtractJob:
    """Extract specific tracks from a video file."""
    logger.info("Extracting audio tracks from video in dir: %s", input_)
    logger.info("Extracting to directory: %s", output)

    files = [str(f) for f in input_.iterdir() if f.is_file()]
    logger.info("Directory files: %s", ", ".join(files))

    job.input_outputs.extend([(f, output / f.name) for f in input_.iterdir() if f.is_file()])
    return job


@extract.command("filter")
@click.option(
    "--include",
    "includes",
    multiple=True,
    type=RegexPattern,
    show_default=False,
    default=[],
    help="Include files matching this pattern.",
)
@click.option(
    "--exclude",
    "excludes",
    multiple=True,
    type=RegexPattern,
    show_default=False,
    default=[],
    help="Exclude files matching this pattern.",
)
@click.option(
    "--ext",
    "extensions",
    help="Specify which video extensions to include in the directory.",
    multiple=True,
    type=click.Choice(VIDEO_EXTENSIONS_NO_DOT, case_sensitive=False),
    default=tuple(VIDEO_EXTENSIONS_NO_DOT),
)
@baet_config()
@processor
def filter_command(
    job: ExtractJob,
    includes: Sequence[Pattern[str]],
    excludes: Sequence[Pattern[str]],
    extensions: Sequence[VideoExtension_NoDot],
) -> ExtractJob:
    """Filter files for selection when providing a directory."""
    escaped_extensions = [re.escape(e) for e in extensions]
    include_extensions = re.compile(rf".*({"|".join(escaped_extensions)})")

    logger.info("Including files with extension: %s", ", ".join([f'"{e}"' for e in escaped_extensions]))

    if includes:
        logger.info("Include file patterns: %s", ", ".join([f'"{p.pattern}"' for p in includes]))

    if excludes:
        logger.info("Exclude file patterns: %s", ", ".join([f'"{p.pattern}"' for p in excludes]))

    job.includes.append(include_extensions)
    job.includes.extend(list(includes))
    job.excludes.extend(list(excludes))
    return job
