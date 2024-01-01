import logging
import sys

import rich
from rich.live import Live
from rich.traceback import install

from BAET import app_console
from BAET._logging import create_logger
from BAET.app_args import get_args
from BAET.extract import MultiTrackAudioBulkExtractor


install(show_locals=True)

VIDEO_EXTENSIONS = [".mp4", ".mkv"]


def main():
    args = get_args()

    if args.debug_options.print_args:
        rich.print(args)
        sys.exit(0)

    if not args.debug_options.logging:
        logging.disable(logging.CRITICAL)

    logger = create_logger()
    logger.info("Building extractor jobs")
    extractor = MultiTrackAudioBulkExtractor(args)

    with Live(extractor, console=app_console):
        logger.info("Running jobs")
        extractor.run_synchronously()

    sys.exit(0)


if __name__ == "__main__":
    main()