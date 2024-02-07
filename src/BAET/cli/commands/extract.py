"""Extract click command."""

import re
from collections.abc import Callable, MutableMapping, Sequence
from dataclasses import dataclass, field
from functools import wraps
from pathlib import Path
from re import Pattern
from typing import Concatenate

import rich_click as click
from rich.console import Group
from rich.live import Live
from rich.padding import Padding
from rich.table import Table

import ffmpeg
from BAET._config.console import app_console
from BAET._config.logging import create_logger
from BAET.cli.help_configuration import baet_config
from BAET.cli.types import RegexPattern
from BAET.constants import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS_NO_DOT, VideoExtension_NoDot
from BAET.display.job_progress import FFmpegJobProgress
from BAET.FFmpeg.jobs import AudioExtractJob
from BAET.FFmpeg.utils import probe_audio_streams
from BAET.typing import AudioStream
from ffmpeg import Stream

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
@click.pass_context
def process(ctx: click.Context, processors: Sequence[Callable[[ExtractJob], ExtractJob]], dry_run: bool) -> None:
    app_console.print(
        "[bold red]This application is currently still in development.",
        "[bold red]Any generated files will overwrite existing files with the same name.",
        end="\n\n",
    )
    # click.confirm("Do you want to continue?", abort=True)

    logger.info("Dry run: %s", dry_run)

    job: ExtractJob = ExtractJob()
    for p in processors:
        job = p(job)

    if not job.includes or not job.excludes:
        default_filter = ctx.invoke(filter_command)
        job = default_filter(job)

    for include in job.includes:
        job.input_outputs = list(filter(lambda x: include.match(x[0].name), job.input_outputs))

    for exclude in job.excludes:
        job.input_outputs = list(filter(lambda x: not exclude.match(x[0].name), job.input_outputs))

    logger.info(
        "Extracting: %s",
        ", ".join(
            f"\n{" " * 4}{file_in!r} -> {file_out.relative_to(file_in.parent)!r}"
            for file_in, file_out in job.input_outputs
        ),
    )

    built = [build_job(io[0], io[1]) for io in job.input_outputs]
    run_synchronously(built)
    # todo: process job


def build_job(file: Path, out_path: Path) -> AudioExtractJob:
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
                    f"{output_path.resolve().as_posix().replace(" ", r"\ ")}",
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
    type=click.Choice(tuple(AUDIO_EXTENSIONS), case_sensitive=False),
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
    show_default="{input parent}/outputs",
    type=click.Path(exists=False, file_okay=False, resolve_path=True, path_type=Path),
)
@click.option(
    "--filetype",
    "-f",
    help="The output filetype.",
    type=click.Choice(tuple(AUDIO_EXTENSIONS), case_sensitive=False),
    default="wav",
)
@baet_config()
@processor
def input_dir(job: ExtractJob, input_: Path, output: Path | None, filetype: str) -> ExtractJob:
    """Extract specific tracks from a video file."""
    if output is None:
        output = input_ / "outputs"

    logger.info("Extracting audio tracks from video in dir: %r", input_)
    logger.info("Extracting to directory: %r", output)
    logger.info("Extracting to filetype: %r", filetype)

    if not filetype.startswith("."):
        filetype = f".{filetype}"

    job.input_outputs.extend([(f, output / f.with_suffix(filetype).name) for f in input_.iterdir() if f.is_file()])
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

    logger.info("Including files with extension: %r", ", ".join([f'"{e}"' for e in escaped_extensions]))

    if includes:
        logger.info("Include file patterns: %r", ", ".join([f'"{p.pattern}"' for p in includes]))

    if excludes:
        logger.info("Exclude file patterns: %r", ", ".join([f'"{p.pattern}"' for p in excludes]))

    job.includes.append(include_extensions)
    job.includes.extend(list(includes))
    job.excludes.extend(list(excludes))
    return job
