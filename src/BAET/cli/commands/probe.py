"""Call FFprobe on a video file."""

from collections import ChainMap, OrderedDict
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rich
import rich_click as click

from BAET._config.logging import create_logger
from BAET.cli.help_configuration import baet_config
from BAET.FFmpeg.probe import probe_file

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
    probed_dict: OrderedDict[str, Any]
    with probe_file(file) as probed:
        if "format" in probed:
            probed_dict = OrderedDict(probed)
            probed_dict.move_to_end("format", last=False)

        return dict(probed)


@click.group(chain=True, invoke_without_command=True)
@baet_config(use_markdown=True)
@click.argument("file", type=click.Path(exists=True, dir_okay=False), required=True)
def probe(file: Path) -> None:
    """Call FFprobe on a video file."""


@probe.result_callback()
def probe_result_callback(commands: list[_key_selector], file: Path) -> None:
    """Run the probe command."""
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
    is_flag=True,
    default=None,
    show_default="Disabled if --audio is specified.",
    help="Include/Exclude format metadata.",
)
def probe_filter(audio: tuple[int, ...], format_: bool | None) -> _key_selector:
    """Specify which audio streams to probe."""
    if audio and format_ is None:
        format_ = False
    elif not audio and format_ is None:
        format_ = True

    logger.info("Filtering streams with index: %r", audio)
    logger.info("Including format information: %s", format_)

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
