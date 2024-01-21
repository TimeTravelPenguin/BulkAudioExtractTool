"""Extract click command."""

from pathlib import Path

import rich_click as click

from BAET._config.logging import create_logger
from BAET.cli.help_configuration import baet_config

logger = create_logger()


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
def extract_tracks(input_path: list[Path]) -> None:
    """Extract click command."""
    logger.info("Extracting audio tracks from video files.")
    for path in input_path:
        kind = "File" if path.is_file() else "Directory"
        logger.info("[bold blue]%s[/]\t%s", kind, click.format_filename(path), extra={"markup": True})

    click.echo(cli_args)


@extract.command()
@click.option("--include", multiple=True, help="Include files matching this pattern.")
def filter():
    pass
