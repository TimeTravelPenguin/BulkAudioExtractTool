import getpass
import sys
from pathlib import Path

import ffmpeg
from ffmpeg.nodes import OutputStream
from rich.console import Console
from rich.markdown import Markdown
from rich.markup import escape

from BAET.AppArgs import AppArgs

from .Console import console, error_console


class AudioExtractor:
    def __init__(
        self,
        file_name: Path,
        app_args: AppArgs,
    ):
        self.file = file_name.resolve(strict=True)
        self.app_args = app_args

    def extract(self):
        output_dir = self.app_args.output_dir

        if not self.app_args.no_output_subdirs:
            output_dir = output_dir / self.file.stem
            # output_dir.mkdir(parents=True, exist_ok=True)

        try:
            audio_streams = self.probe_audio_stream()
        except ffmpeg.Error as e:
            error_console.print(e.stderr)
            return None
        except ValueError as e:
            error_console.print(e)
            return None

        input_file = ffmpeg.input(str(self.file))

        outputs = []
        for stream in audio_streams:
            outputs.append(self.create_output(input_file, stream))

        output = ffmpeg.merge_outputs(*outputs)
        self.print_ffmpeg_cmd(output)

    def create_output(self, input_file, stream):
        index = stream["index"]
        audio_stream = input_file[f"a:{index}"]
        return ffmpeg.output(
            audio_stream,
            f"{self.file.stem}_track{index}.{self.app_args.file_type}",
            acodec=self.app_args.acodec,
        )

    def probe_audio_stream(self):
        probe = ffmpeg.probe(self.file)

        audio_streams = [
            stream
            for stream in probe["streams"]
            if "codec_type" in stream and stream["codec_type"] == "audio"
        ]

        if not audio_streams:
            raise ValueError("No audio streams found")

        return audio_streams

    def print_ffmpeg_cmd(self, output):
        compiled = " ".join(ffmpeg.compile(output))

        md_user = f"{getpass.getuser()}:~$"
        cmd = Markdown(f"```console\n{md_user} {compiled}\n```")

        console.print(cmd)
