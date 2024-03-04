"""Extract click command."""

import re
from collections.abc import Callable, MutableMapping, Sequence
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from re import Pattern
from typing import Concatenate

import rich.repr
import rich_click as click
from rich.console import Group
from rich.live import Live
from rich.padding import Padding
from rich.pretty import pretty_repr
from rich.table import Table

import ffmpeg
from BAET._config.console import app_console
from BAET._config.logging import create_logger
from BAET.cli.help_configuration import baet_config
from BAET.constants import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS_NO_DOT, VideoExtension_NoDot
from BAET.display.job_progress import FFmpegJobProgress
from BAET.FFmpeg.jobs import AudioExtractJob
from BAET.FFmpeg.probe import probe_audio_streams
from BAET.helpers.string_helpers import pretty_join
from BAET.typing import AudioStream
from ffmpeg import Stream

logger = create_logger()


@rich.repr.auto()
@dataclass()
class ExtractJob:
    """Dataclass for holding extract job information."""

    input_outputs: list[tuple[Path, Path]] = field(default_factory=lambda: [])
    includes: list[Pattern[str]] = field(default_factory=lambda: [])
    excludes: list[Pattern[str]] = field(default_factory=lambda: [])
    include_extensions: list[Pattern[str]] = field(default_factory=lambda: [])


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
    "--overwrite",
    is_flag=True,
    default=False,
    show_default=True,
    help="Overwrite existing files.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run without actually producing any output.",
)
@baet_config()
def extract(dry_run: bool, overwrite: bool) -> None:
    """Extract click command."""


@extract.result_callback()
@click.pass_context
def process(
    ctx: click.Context,
    processors: Sequence[Callable[[ExtractJob], ExtractJob]],
    dry_run: bool,
    overwrite: bool,
) -> None:
    """Process the extract command."""
    if not overwrite:
        app_console.print(
            "[bold red]This application is currently still in development.",
            "[bold red]Any generated files will overwrite existing files with the same name.",
            end="\n\n",
        )

        click.confirm("Do you want to continue?", abort=True)

    logger.info("Dry run: %s", dry_run)

    job: ExtractJob = ExtractJob()
    for p in processors:
        job = p(job)

    if not job.include_extensions:
        default_filter = ctx.invoke(filter_command, extensions=[re.escape(e) for e in VIDEO_EXTENSIONS_NO_DOT])
        job = default_filter(job)

    logger.debug("Job (Prefiltered Inputs)::\n%s", pretty_repr(job))
    logger.info(pretty_join(job.input_outputs, "Prefiltered inputs", formatter=lambda inout: f"{inout[0]!r}"))

    for include in job.includes:
        job.input_outputs = list(filter(lambda x: include.match(x[0].name), job.input_outputs))

    for exclude in job.excludes:
        job.input_outputs = list(filter(lambda x: not exclude.match(x[0].name), job.input_outputs))

    job.input_outputs = list(
        filter(lambda x: any(ext.match(x[0].name) for ext in job.include_extensions), list(job.input_outputs))
    )

    logger.debug("Job (Filtered Inputs):\n%s", pretty_repr(job))
    logger.info(pretty_join(job.input_outputs, "Filtered inputs", formatter=lambda inout: f"{inout[0]!r}"))

    logger.info(
        pretty_join(
            job.input_outputs,
            "Extracting",
            formatter=lambda inout: f"{inout[0]!r} -> {inout[1].relative_to(inout[0].parent)!r}",
        )
    )

    built = [build_job(io[0], io[1]) for io in job.input_outputs]

    if not dry_run:
        run_synchronously(built)

    logger.info("Finished extracting.")


def build_job(file: Path, out_path: Path) -> AudioExtractJob:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    audio_streams: list[AudioStream] = []
    indexed_outputs: MutableMapping[int, Stream] = {}

    file = file.expanduser()
    with probe_audio_streams(file) as streams:
        for idx, stream in enumerate(streams):
            ffmpeg_input = ffmpeg.input(str(file))
            stream_index = stream["index"]
            output_path = out_path.with_stem(f"{out_path.stem}_track{stream_index}")
            sample_rate = stream.get(
                "sample_rate",
                44100,
            )

            audio_streams.append(stream)

            indexed_outputs[stream_index] = (
                ffmpeg.output(
                    ffmpeg_input[f"a:{idx}"],
                    f"{output_path.resolve().as_posix()}",  # .replace(" ", r"\ ")}",
                    format=output_path.suffix.lstrip("."),
                    acodec="pcm_s16le",
                    audio_bitrate=sample_rate,
                )
                .overwrite_output()
                .global_args("-progress", "-", "-nostats")
            )

    return AudioExtractJob(file, audio_streams, indexed_outputs)


def run_synchronously(jobs: list[AudioExtractJob]) -> None:
    display = Table.grid()

    job_progresses = [FFmpegJobProgress(job) for job in jobs]
    display.add_row(Padding(Group(*job_progresses), pad=(1, 2)))

    logger.info("Starting synchronous execution of queued jobs")
    with Live(display, console=app_console):
        for progress in job_progresses:
            logger.info("Starting job %r", {progress.job.input_file})
            progress.start()


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
    default=None,
)
@click.option(
    "--filetype",
    "-f",
    help="The output filetype.",
    required=False,
    type=click.Choice(AUDIO_EXTENSIONS, case_sensitive=False),
    default=None,
)
@baet_config()
@processor
def input_file(job: ExtractJob, input_: Path, output: Path | None, filetype: str | None) -> ExtractJob:
    """Extract specific tracks from a video file."""
    if filetype is not None and not filetype.startswith("."):
        filetype = f".{filetype}"

    if output is None:
        out = input_.with_suffix(filetype or ".wav")
    elif output.is_file():
        if filetype:
            logger.warning("Provided a file output and filetype, ignoring filetype.")
        out = output
    elif output.is_dir():
        out = output / input_.with_suffix(filetype or ".wav").name
    else:
        raise click.BadParameter(f"Invalid output path: {output!r}", param_hint="output")

    logger.info("Extracting audio tracks from video file: %r", input_)
    logger.info("Extracting to: %r", out)

    job.input_outputs.append((input_, out))
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
    default=None,
    show_default="[INPUT]",
    type=click.Path(exists=False, file_okay=False, resolve_path=True, path_type=Path),
)
@click.option(
    "--filetype",
    "-f",
    help="The output filetype.",
    type=click.Choice(AUDIO_EXTENSIONS, case_sensitive=False),
    default="wav",
)
@baet_config()
@processor
def input_dir(job: ExtractJob, input_: Path, output: Path | None, filetype: str) -> ExtractJob:
    """Extract specific tracks from a video file."""
    if output is None:
        output = input_

    logger.info("Extracting audio tracks from video in dir: %r", input_)
    logger.info("Extracting to directory: %r", output)
    logger.info("Extracting to filetype: %r", filetype)

    if not filetype.startswith("."):
        filetype = f".{filetype}"

    for input_file in input_.iterdir():
        if not input_file.is_file():
            continue
        file_output = output / input_file.stem / input_file.with_suffix(filetype).name
        job.input_outputs.append((input_file, file_output))

    return job


@extract.command("filter")
@click.option(
    "--include",
    "includes",
    multiple=True,
    show_default=False,
    default=[],
    help="Include files matching this pattern.",
)
@click.option(
    "--exclude",
    "excludes",
    multiple=True,
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
    default=VIDEO_EXTENSIONS_NO_DOT,
)
@click.option(
    "--case-sensitive/--case-insensitive",
    "case_sensitive",
    default=False,
    help="Whether to match case sensitively.",
    show_default=True,
)
@baet_config()
@processor
def filter_command(
    job: ExtractJob,
    includes: Sequence[str],
    excludes: Sequence[str],
    extensions: Sequence[VideoExtension_NoDot],
    case_sensitive: bool,
) -> ExtractJob:
    """Filter files for selection when providing a directory."""
    flag = re.IGNORECASE if not case_sensitive else re.NOFLAG

    include_patterns = []
    exclude_patterns = []
    extensions_patterns = []

    pattern_list_pairs = zip(
        [includes, excludes, extensions],
        [include_patterns, exclude_patterns, extensions_patterns],
        strict=True,
    )

    try:
        for patterns, lst in pattern_list_pairs:
            for pattern in patterns:
                lst.append(re.compile(pattern, flag))
    except re.error as e:
        logger.error("Error: %s", e)
        raise click.BadParameter("Invalid pattern", param_hint="pattern") from e

    include_patterns = [re.compile(p, flag) for p in includes]
    exclude_patterns = [re.compile(p, flag) for p in excludes]
    extensions_patterns = [re.compile(rf".*\.{re.escape(e)}$", flag) for e in extensions]

    logger.info("Filtering is case sensitivity: %s", case_sensitive)

    if includes:
        logger.info(pretty_join(includes, "Include file patterns"))

    if excludes:
        logger.info(pretty_join(excludes, "Exclude file patterns"))

    if extensions:
        logger.info(pretty_join(extensions, "Including extensions"))
        logger.info(pretty_join(extensions_patterns, "Including' extensions", formatter=lambda p: p.pattern))

    job.includes.extend(include_patterns)
    job.excludes.extend(exclude_patterns)
    job.include_extensions.extend(extensions_patterns)

    return job
