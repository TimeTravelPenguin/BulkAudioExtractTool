"""Application commandline interface."""

import re

import rich_click as click

from BAET._config.logging import create_logger
from BAET.cli.help_configuration import make_help_config

from .command_args import CliArgs, pass_cli_args
from .commands import extract, probe

logger = create_logger()

file_type_pattern = re.compile(r"^\.?(\w+)$")


@click.group()
@click.rich_config(help_config=make_help_config())
# @BaetConfig()
@click.version_option(prog_name="BAET", package_name="BAET", message="%(prog)s v%(version)s")
@click.option("--logging", "-L", is_flag=True, help="Run the application with logging.")
@pass_cli_args
def cli(cli_args: CliArgs, logging: bool) -> None:
    """BAET commandline interface."""
    cli_args.logging = logging


cli.add_command(extract)
cli.add_command(probe)


def test() -> None:
    """Test the CLI."""
    cli()
