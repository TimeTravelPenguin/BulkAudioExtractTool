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

    if args.debug_options.logging:
        log_path = Path("~/.baet").expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        log_file = log_path / f"logs_{datetime.now()}.txt"
        log_file.touch()

        configure_logging(enable_logging=True, file_out=log_file)
    else:
        configure_logging(enable_logging=False, file_out=None)

    logger = create_logger()
    extractor = MultiTrackAudioBulkExtractor(args)

    with Live(extractor, console=app_console):
        logger.info("Running jobs")
        extractor.run_synchronously()

    sys.exit(0)
