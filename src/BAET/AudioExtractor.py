import getpass
from pathlib import Path

import ffmpeg
from rich.markdown import Markdown

from BAET.AppArgs import AppArgs
from BAET.Console import console, error_console
from BAET.Logging import info_logger


def print_ffmpeg_cmd(output):
    compiled = " ".join(ffmpeg.compile(output))

    md_user = f"{getpass.getuser()}:~$"
    cmd = Markdown(f"```console\n{md_user} {compiled}\n```")

    console.print(cmd)


class AudioExtractor:
    def __init__(
        self,
        file: Path,
        app_args: AppArgs,
    ):
        self.file = file
        self.output_dir = app_args.output_dir
        self.input_filters = app_args.input_filters
        self.output_configuration = app_args.output_configuration
        self.debug_options = app_args.debug_options

        self.output_dir = (
            self.output_dir
            if not self.output_configuration.no_output_subdirs
            else self.output_dir / self.file.stem
        )

    def extract(self):
        try:
            audio_streams = self.probe_audio_stream()
            info_logger.info("Found %d audio streams", len(audio_streams))
        except ffmpeg.Error as e:
            info_logger.critical("Found no audio streams")
            error_console.print(e.stderr)
            return None
        except ValueError as e:
            info_logger.critical("Found no audio streams")
            error_console.print(e)
            return None

        ffmpeg_input = ffmpeg.input(str(self.file))

        info_logger.info("Creating ffmpeg command to extract each stream")

        outputs = []
        for stream in audio_streams:
            out = self.create_output(ffmpeg_input, stream)
            outputs.append(out)

        info_logger.info("Extracting audio to %s", self.output_dir)

        if not self.output_configuration.output_streams_separately:
            output = ffmpeg.merge_outputs(*outputs)
            self._run(output)
            return

        for output in outputs:
            self._run(output)

    def _run(self, output):
        if self.output_configuration.overwrite_existing:
            output = ffmpeg.overwrite_output(output)
        if self.debug_options.show_ffmpeg_cmd:
            print(output)
        if not self.debug_options.dry_run:
            output.run()

    def create_output(self, input_file, stream):
        index = stream["index"]
        audio_stream = input_file[f"a:{index - 1}"]

        self.output_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            f"{self.file.stem}_track{index}.{self.output_configuration.file_type}"
        )

        info_logger.info("Creating output file %s", str(self.output_dir / filename))

        return ffmpeg.output(
            audio_stream,
            str(self.output_dir / filename),
            acodec=self.output_configuration.acodec,
            audio_bitrate=(
                stream["sample_rate"] or self.output_configuration.fallback_sample_rate
            ),
            format=self.output_configuration.file_type,
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
