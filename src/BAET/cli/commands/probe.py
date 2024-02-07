"""Call FFprobe on a video file."""

from collections import ChainMap, OrderedDict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rich
import rich_click as click

import ffmpeg
from BAET._config.logging import create_logger
from BAET.cli.help_configuration import baet_config

logger = create_logger()

type _key_selector = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass()
class ProbeContext:
    """Context for the probe command."""

    file: Path
    streams_only: bool
    tracks: tuple[int, ...] | None
    key: tuple[str, ...] | None


def _probe_file(file: Path) -> dict[str, Any]:
    logger.info('Probing file "%s"', file)

    try:
        probed: OrderedDict[str, Any] = OrderedDict(ffmpeg.probe(file))
    except ffmpeg.Error as e:
        err: str = e.stderr.decode()
        raise click.ClickException(f"Error probing file {err.strip().splitlines()[-1]}") from e

    if "format" in probed:
        probed.move_to_end("format", last=False)

    return dict(probed)


@click.group(chain=True, invoke_without_command=True)
@baet_config(use_markdown=True)
@click.argument("file", type=click.Path(exists=True, dir_okay=False), required=True)
def probe(file: Path) -> None:
    """Call FFprobe on a video file."""


@probe.result_callback()
def probe_result_callback(commands: list[_key_selector], file: Path) -> None:
    """Run the probe command."""
    logger.info("Running probe result_callback.")

    probed: dict[str, Any] = _probe_file(file)

    if not commands:
        rich.print_json(data=probed)
        return

    filtered: dict[str, Any] = dict(ChainMap(*[command(probed) for command in commands]))

    rich.print_json(data=filtered)


@probe.command(name="filter")
@click.option(
    "-a",
    "--audio",
    multiple=True,
    help="Specific audio track index to probe. Can be specified multiple times.",
    type=click.IntRange(min=0),
)
@click.option(
    "--format/--no-format",
    "-f/-nf",
    "format_",
    default=True,
    show_default="Enabled",
    help="Include/Exclude format metadata.",
)
def probe_filter(audio: tuple[int, ...], format_: bool | None) -> _key_selector:
    """Specify which audio streams to probe."""
    logger.info("Called stream with: %s", audio)

    def processor(meta: dict[str, Any]) -> Any:
        if "streams" not in meta:
            raise click.ClickException("No stream metadata found")

        format_dict = {"format": meta["format"]} if format_ else {}
        return format_dict | {"streams": _filter_streams(audio, meta["streams"])}

    return processor


def _filter_streams(indexes: Sequence[int], streams: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not indexes:
        return streams

    return [stream for stream in streams if stream["index"] in indexes]
