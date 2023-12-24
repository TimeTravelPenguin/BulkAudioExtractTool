import contextlib
import getpass
import sys
from pathlib import Path
from subprocess import Popen

import ffmpeg
from ffmpeg.nodes import InputNode
from rich.markdown import Markdown

from BAET.AppArgs import AppArgs
from BAET.Console import console, error_console
from BAET.Logging import info_logger


def print_ffmpeg_cmd(output):
    compiled = " ".join(ffmpeg.compile(output))

    md_user = f"{getpass.getuser()}:~$"
    cmd = Markdown(f"```console\n{md_user} {compiled}\n```")

    console.print(cmd)
    console.print()


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
        ffmpeg_input: InputNode = ffmpeg.input(self.file)
        workers = []

        with probe_audio_streams(self.file) as audio_streams:
            # Check: does the indexing of audio stream relate to ffprobe index
            # or to the index of the collected audio streams in ffmpeg_input["a:index"]?
            for index, stream in enumerate(audio_streams):
                # index = stream["index"]

                out = self._create_workers(
                    ffmpeg_input,
                    index,
                    stream["sample_rate"] or self.output_configuration.sample_rate,
                )

                workers.append(out)

        info_logger.info("Extracting audio to %s", self.output_dir)

        # if not self.output_configuration.output_streams_separately:
        #     output = ffmpeg.merge_outputs(*worker_pairs)
        #     self._run(output)
        #     return
        #
        # for output in worker_pairs:
        #     self._run(output)

        try:
            for output in workers:
                self._run_workers(output)
        except Exception as e:
            info_logger.critical("%s: %s", type(e).__name__, e)
            error_console.print_exception()
            raise e

    def _run_workers(self, ffmpeg_output):
        # if self.debug_options.show_ffmpeg_cmd:
        #     print_ffmpeg_cmd(ffmpeg_write)

        if self.debug_options.dry_run:
            return

        proc: Popen[bytes] = ffmpeg_output.run_async(pipe_stdout=True)

        while proc.poll() is None:
            output = proc.stdout.readline().decode("utf-8")
            console.print(output)

        if proc.returncode != 0:
            info_logger.critical("Return code: %s", proc.returncode)
            sys.exit(-1)
            # todo: hangs here :(

            # progress_text = input_data.decode("utf-8")
            # console.print(progress_text)

            # proc_write.stdin.write(input_data)

            # Look for "frame=xx"
            # if progress_text.startswith("frame="):
            #     frame = int(progress_text.partition("=")[-1])  # Get the frame number
            #     console.print(f"q: {frame}")

        proc.wait()

    def _create_workers(
        self, ffmpeg_input: InputNode, stream_index: int, sample_rate: int
    ):
        self.output_dir.mkdir(parents=True, exist_ok=True)

        output_filename = Path(
            f"{self.file.stem}_track{stream_index}.{self.output_configuration.file_type}"
        )

        # TODO: MOVE
        info_logger.info(
            "Creating output dir %s", self.output_dir / output_filename.stem
        )

        opt_kwargs = {
            "acodec": self.output_configuration.acodec,
            "audio_bitrate": sample_rate
            or self.output_configuration.fallback_sample_rate,
            "format": self.output_configuration.file_type,
        }

        output = ffmpeg_input[f"a:{stream_index}"].output(
            str(output_filename), **opt_kwargs
        )

        if self.output_configuration.overwrite_existing:
            output = output.overwrite_output()

        return output