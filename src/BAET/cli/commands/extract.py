"""Extract click command."""

from pathlib import Path

import rich_click as click

from BAET._config.logging import create_logger
from BAET.cli.help_configuration import baet_config

from ..command_args import CliOptions, pass_cli_options

logger = create_logger()


@click.group()
@baet_config()
def extract() -> None:
    """Extract the audio track(s) of a video."""


@extract.command(name="tracks", help="Extract audio tracks from video files.")
@baet_config()
@click.option(
    "--input-path",
    "-i",
    required=True,
    type=click.Path(exists=True, resolve_path=True, path_type=Path),
    multiple=True,
    show_default="current dir",
    help="Input file or directory path.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    show_default=True,
    help="Run without actually producing any output.",
)
@pass_cli_options
def extract_tracks(cli_args: CliOptions, input_path: list[Path], dry_run: bool) -> None:
    """Extract click command."""
    cli_args.dry_run = dry_run

    if not cli_args.logging:
        return

    for path in input_path:
        kind = "File" if path.is_file() else "Directory"
        logger.info("[bold blue]%s[/]\t%s", kind, click.format_filename(path), extra={"markup": True})

    click.echo(cli_args)
