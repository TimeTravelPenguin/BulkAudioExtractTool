import sys

import rich
from rich.traceback import install

from BAET.AppArgs import GetArgs
from BAET.AudioExtractor import AudioExtractor
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

    for file in files:
        info_logger.info("Processing input file '%s'", file)
        ex = AudioExtractor(file, args)
        ex.extract()


if __name__ == "__main__":
    main()
