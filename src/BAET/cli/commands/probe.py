"""Call FFprobe on a video file."""

from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import ffmpeg
import rich
import rich_click as click
from rich_click import Context, Option

from BAET._config.logging import create_logger
from BAET.cli.help_configuration import make_help_config

logger = create_logger()


def _ffprobe_file(ctx: Context, param: Option, value: str) -> tuple[str, Any]:
    logger.info('Probing file "%s"', value)

    try:
        probed = ffmpeg.probe(value)
    except ffmpeg.Error as e:
        raise click.BadParameter(f"Error probing file: {e.stderr}", param=param) from e

    return value, probed


@dataclass()
class ProbeContext:
    """Context for the probe command."""

    file: Path
    streams_only: bool
    tracks: tuple[int, ...] | None
    key: tuple[str, ...] | None


@click.command()
@click.rich_config(help_config=make_help_config())
@click.option(
    "--streams-only",
    "-s",
    is_flag=True,
    show_default=True,
    help="Only show the stream metadata(s), not the format information.",
)
@click.option(
    "--track",
    "-t",
    "tracks",
    type=int,
    multiple=True,
    default=None,
    show_default="All tracks",
    help="Track number to extract. This will implicitly set --streams-only.",
)
@click.argument(
    "file",
    type=click.Path(exists=True, resolve_path=True, dir_okay=False, path_type=Path),
    callback=_ffprobe_file,
    required=True,
)
def probe(
    file: tuple[Path, dict[str, Any]],
    streams_only: bool,
    tracks: tuple[int, ...] | None,
) -> None:
    """Call FFprobe on a video file."""
    file_path, probed = file
    probed = OrderedDict(probed)

    if tracks:
        streams_only = True

    if "format" in probed:
        probed.move_to_end("format", last=False)

    streams: list[dict[str, Any]] | None = probed.get("streams")

    if streams is None:
        raise click.ClickException(f"No streams found in the file {file_path}")

    if tracks and streams:

        def index_in_tracks(stream: dict[str, Any]) -> bool:
            return stream["index"] in tracks

        streams = list(filter(index_in_tracks, streams))

    rich.print("Results for file:", file_path)

    if streams_only:
        rich.print_json(data={"streams": streams})
        return

    probed["streams"] = streams
    rich.print_json(data=probed)
