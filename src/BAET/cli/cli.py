"""Application commandline interface."""

import re

import rich_click as click

from BAET._config.logging import configure_logging, create_logger
from BAET.cli.help_configuration import baet_config

from .commands import extract, probe

logger = create_logger()

file_type_pattern = re.compile(r"^\.?(\w+)$")


@click.group()
@baet_config(use_markdown=True)
@click.version_option(prog_name="BAET", package_name="BAET", message="%(prog)s v%(version)s")
@click.option("--logging", "-L", is_flag=True, help="Run the application with logging.")
def cli(logging: bool) -> None:
    """**Bulk Audio Extraction Tool (BAET)**

    This tool provides a simple way to extract audio from video files.
    - You can use --help on any command to get more information.
    """
    configure_logging(enable_logging=logging)


cli.add_command(extract.extract)
cli.add_command(probe.probe)


def test() -> None:
    """Test the CLI."""
    cli()
