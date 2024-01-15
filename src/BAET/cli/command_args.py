"""Context objects for commands with Click."""
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from re import Pattern

import click


@dataclass()
class InOutArgs:
    """Argument for a command."""

    inputs: Sequence[Path]
    output: Path


@dataclass()
class InFilterArgs:
    """Argument for a command."""

    include_pattern: Pattern[str]
    exclude_pattern: Pattern[str] | None


@dataclass()
class Output:
    """Argument for a command."""

    verbose: bool
    dry_run: bool


@dataclass()
class CliOptions:
    """Argument for a command."""

    logging: bool = False
    dry_run: bool = False


pass_cli_options = click.make_pass_decorator(CliOptions, ensure=True)
