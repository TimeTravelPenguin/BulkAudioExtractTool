import sys
from pathlib import Path

import ffmpeg
from rich import print as pprint

from BAET.AppArgs import GetArgs


def get_files_in_dir(dir_path: Path, extension: list[str]) -> list[Path]:
    """Get all files in a directory with the specified extension.

    Args:
        dir_path (Path): Path to directory.
        extension (str): File extension to filter by.

    Returns:
        list[Path]: List of files in the directory with the specified extension.
    """
    return [file for file in dir_path.iterdir() if file.suffix in extension]


def main():
    args = GetArgs()

    files = get_files_in_dir(args.input_dir, [".mp4", ".mkv"])

    indexes = set()
    for file in files:
        pprint(file)

        try:
            probe = ffmpeg.probe(file)
        except ffmpeg.Error as e:
            print(e.stderr, file=sys.stderr)
            sys.exit(1)

        outputs = []
        audio_streams = [
            stream["index"]
            for stream in probe["streams"]
            if "codec_type" in stream and stream["codec_type"] == "audio"
        ]

        if not audio_streams:
            print("No audio streams found", file=sys.stderr)
            sys.exit(1)

        input = ffmpeg.input(str(file))

        for i in audio_streams:
            stream = input[f"a:{i}"]
            outputs.append(stream.output(f"output{i}.aac", acodec="copy"))

        output = ffmpeg.merge_outputs(*outputs)
        cmd = " ".join(output.compile())
        print(cmd)

        # output.run()


if __name__ == "__main__":
    main()
