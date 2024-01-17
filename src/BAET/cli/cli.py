"""Application commandline interface."""

import re

import rich_click as click

from BAET._config.logging import create_logger
from BAET.cli.help_configuration import BaetConfig

from .command_args import CliOptions, pass_cli_options
from .commands import extract, probe

logger = create_logger()

file_type_pattern = re.compile(r"^\.?(\w+)$")


@click.group()
@BaetConfig(use_markdown=True)
@click.version_option(prog_name="BAET", package_name="BAET", message="%(prog)s v%(version)s")
@click.option("--logging", "-L", is_flag=True, help="Run the application with logging.")
@pass_cli_options
def cli(cli_args: CliOptions, logging: bool) -> None:
    """**Bulk Audio Extraction Tool (BAET)**

    This tool provides a simple way to extract audio from video files.
    - You can use --help on any command to get more information.
    """
    cli_args.logging = logging


cli.add_command(extract)
cli.add_command(probe)


def test() -> None:
    """Test the CLI."""
    cli()


if __name__ == "__main__":
    test()
