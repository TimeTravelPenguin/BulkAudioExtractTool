import sys

import rich
from rich.console import Group
from rich.live import Live
from rich.traceback import install

from BAET import app_console
from BAET._logging import ConsoleLogDisplay
from BAET.app_args import get_args
from BAET.extract import MultiTrackAudioBulkExtractor


install(show_locals=True)

VIDEO_EXTENSIONS = [".mp4", ".mkv"]


def main():
    args = get_args()

    if args.debug_options.print_args:
        rich.print(args)
        sys.exit(0)

    log_display = ConsoleLogDisplay()
    if args.debug_options.logging:
        log_display.enabled = True

    with log_display as logger:
        logger.info("Building extractor jobs")
        ex = MultiTrackAudioBulkExtractor(args)

        group = Group(log_display, ex)
        with Live(group, refresh_per_second=10, console=app_console) as live:
            logger.info("Running jobs")
            ex.run_synchronously()

    sys.exit(0)


if __name__ == "__main__":
    main()