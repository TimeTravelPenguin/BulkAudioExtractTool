from pathlib import Path

from BAET.AppArgs import AppArgs


class AudioExtractor:
    def __init__(
        self,
        file_name: str,
        app_args: AppArgs,
    ):
        if not file_name:
            pass
        self.file = (app_args.input_dir / file_name).resolve(strict=True)
        self.app_args = app_args
