import contextlib
import getpass
from pathlib import Path

import ffmpeg
from ffmpeg.nodes import Stream
from rich.markdown import Markdown

from BAET.AppArgs import AppArgs
from BAET.Console import console, error_console
from BAET.FFmpegExtract.FFmpegProcess import FFmpegProcessGroup, ProbedOutput
from BAET.Logging import info_logger


@contextlib.contextmanager
def probe_audio_streams(file: Path):
    try:
        info_logger.info('Probing "%s"', file)
        probe = ffmpeg.probe(file)

        audio_streams = [
            stream
            for stream in probe["streams"]
            if "codec_type" in stream and stream["codec_type"] == "audio"
        ]

        if not audio_streams:
            raise ValueError("No audio streams found")

        info_logger.info("Found %d audio streams", len(audio_streams))
        yield audio_streams

    except (ffmpeg.Error, ValueError) as e:
        info_logger.critical("%s: %s", type(e).__name__, e)
        error_console.print_exception()
        raise e


def print_ffmpeg_cmd(output: Stream):
    compiled = " ".join(ffmpeg.compile(output))

    md_user = f"{getpass.getuser()}:~$"
    cmd = Markdown(f"```console\n{md_user} {compiled}\n```")

    console.print(cmd)
    console.print()


class FFmpegProcBuilder:
    def __init__(self, app_args: AppArgs):
        self.input_dir = app_args.input_dir
        self.output_dir = app_args.output_dir
        self.input_filters = app_args.input_filters
        self.output_configuration = app_args.output_configuration
        self.debug_options = app_args.debug_options

    def __call__(self, file: Path):
        output = self.build_args(file)

        # for output in outputs:
        #     if self.debug_options.show_ffmpeg_cmd:
        #         print_ffmpeg_cmd(output)

        # TODO
        output.run_synchronously()

    def create_output_subdir(self, file: Path):
        return (
            self.output_dir
            if not self.output_configuration.no_output_subdirs
            else self.output_dir / file.stem
        )

    def create_output_filepath(
        self, file: Path, stream_index: int, sample_rate: int | None
    ) -> Path:
        filename = Path(
            f"{file.stem}_track{stream_index}.{self.output_configuration.file_type}"
        )

        out_path = (
            self.output_dir
            if self.output_configuration.no_output_subdirs
            else self.output_dir / file.stem
        )

        info_logger.info('Preparing to write "%s" to "%s"', filename, out_path)

        out_path.mkdir(parents=True, exist_ok=True)
        return out_path / filename

    def create_outputs_for_file(
        self,
        file: Path,
        probe_info: list[dict],
    ) -> list[ProbedOutput]:
        ffmpeg_input = ffmpeg.input(str(file))

        outputs: list[ProbedOutput] = []
        for idx, stream in enumerate(probe_info):
            sample_rate = (
                stream.get("sample_rate", None)
                or self.output_configuration.fallback_sample_rate
            )

            output = ffmpeg.output(
                ffmpeg_input[f"a:{idx}"],
                str(self.create_output_filepath(file, stream["index"], sample_rate)),
                acodec=self.output_configuration.acodec,
                audio_bitrate=sample_rate
                or self.output_configuration.fallback_sample_rate,
            )

            outputs.append(ProbedOutput(output, stream))

        return outputs

    def build_args(self, file: Path) -> FFmpegProcessGroup:
        if not file.resolve(strict=True).is_file():
            raise FileNotFoundError(f'The file "{file}" does not exist')

        with probe_audio_streams(file) as audio_streams:
            return FFmpegProcessGroup(
                self.create_outputs_for_file(file, audio_streams),
                self.output_configuration.overwrite_existing,
            )