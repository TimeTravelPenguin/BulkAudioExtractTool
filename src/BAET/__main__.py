import sys
from datetime import datetime
from pathlib import Path

import rich
from rich.live import Live
from rich.traceback import install

from BAET import app_console, configure_logging, create_logger
from BAET.app_args import get_args
from BAET.extract import MultiTrackAudioBulkExtractor

install(show_locals=True)


def main() -> None:
    args = get_args()

    if args.debug_options.print_args:
        rich.print(args)
        sys.exit(0)

    if not args.debug_options.logging:
        log_path = Path("~/.baet").expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / f"logs_{datetime.now()}.txt"
        log_file.touch()

        configure_logging(enable_logging=True, file_out=log_file)

    logger = create_logger()
    logger.info("Building extractor jobs")
    extractor = MultiTrackAudioBulkExtractor(args)

    with Live(extractor, console=app_console):
        logger.info("Running jobs")
        extractor.run_synchronously()

    sys.exit(0)
