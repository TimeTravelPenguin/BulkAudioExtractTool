import importlib.metadata
import subprocess
from os import PathLike
from shutil import which
from subprocess import CalledProcessError

from .console import error_console
from .logging import create_logger

logger = create_logger()


def app_version() -> str:
    return importlib.metadata.version("BAET")


def which_ffmpeg() -> str | PathLike[str] | None:
    return which("ffmpeg")


def get_ffmpeg_version() -> str | None:
    try:
        ffmpeg = which_ffmpeg()

        if not ffmpeg:
            return None

        proc = subprocess.run([ffmpeg, "-version"], capture_output=True, check=True)

        if proc.returncode != 0:
            err = proc.stderr.decode("utf-8")
            raise RuntimeError(f"FFmpeg returned non-zero exit code when getting version:\n{err}")

        output = proc.stdout.decode("utf-8")
        return output[14 : output.find("Copyright")].strip()

    except CalledProcessError as e:
        logger.critical("FFmpeg exited with a non-zero exit code.\n%s: %s", type(e).__name__, e)
        error_console.print_exception()
        raise e
    except RuntimeError as e:
        logger.critical("%s: %s", type(e).__name__, e)
        error_console.print_exception()
        raise e


class FFmpegVersionInfo:
    def __init__(self) -> None:
        self._version: str | None = None

    @property
    def version(self) -> str:
        if not self._version:
            self._version = get_ffmpeg_version()

        return self._version or "None"

    def __str__(self) -> str:
        return self.version


ffmpeg_version_info = FFmpegVersionInfo()

if __name__ == "__main__":
    version_info = FFmpegVersionInfo()
    print("Version:", version_info)
