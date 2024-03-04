"""Application commandline interface."""

import rich_click as click

from BAET._config.logging import app_logger, configure_logging, create_logger
from BAET.cli.help_configuration import baet_config

from .commands import extract, probe

logger = create_logger()


@click.group("baet")
@baet_config(use_markdown=True)
@click.version_option(prog_name="BAET", package_name="BAET", message="%(prog)s v%(version)s")
@click.option("--logging", "-L", help="Run the application with logging.", count=True)
def cli(logging: int) -> None:
    """**Bulk Audio Extraction Tool (BAET)**

    This tool provides a simple way to extract audio from video files.
    - You can use --help on any command to get more information.
    """  # noqa: D400
    configure_logging(enable_logging=logging > 0)
    if logging > 1:
        app_logger.setLevel("DEBUG")

    # Currently only two levels of verbosity for info/debug level logging
    logger.info("Logging verbosity: %s", max(0, min(2, logging)))


cli.add_command(extract.extract)
cli.add_command(probe.probe)
