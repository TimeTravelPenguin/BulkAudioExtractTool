"""Bulk Audio Export Tool (BAET) is a command line tool for exporting audio tracks from video files in bulk."""

import sys

from rich.traceback import install

from BAET.cli.cli import cli

# Enable rich traceback
install(show_locals=True)


def main() -> None:
    """Entry point for BAET."""
    cli()
    sys.exit(0)
