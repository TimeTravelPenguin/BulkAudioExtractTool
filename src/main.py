import sys

import rich
from rich.traceback import install

from BAET.AppArgs import GetArgs
from BAET.Console import app_console
from BAET.FFmpegExtract import FFmpegExtractor
from BAET.Logging import info_logger

install(show_locals=True)

VIDEO_EXTENSIONS = [".mp4", ".mkv"]


def main():
    args = GetArgs()

    if not args.debug_options.logging:
        info_logger.disabled = True

    if args.debug_options.print_args:
        rich.print(args)
        sys.exit(0)

    files = [
        file for file in args.input_dir.iterdir() if file.suffix in VIDEO_EXTENSIONS
    ]

    if not files:
        path = args.input_dir.absolute()
        app_console.print(f'No video files found in "[link file://{path}]{path}[/]".')
        sys.exit(0)

    ex = FFmpegExtractor(args)
    ex.run_synchronously()

    sys.exit(0)


if __name__ == "__main__":
    main()
