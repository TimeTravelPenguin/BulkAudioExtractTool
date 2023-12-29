import logging

from rich.logging import RichHandler

from BAET._console import app_console


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True, console=app_console)],
)

console_logger = logging.getLogger("console_logger")


class LevelFilter(logging.Filter):
    def __init__(self, loglevel: int) -> None:
        super().__init__()
        self.loglevel = loglevel

    def filter(self, record):
        return record.levelno == self.loglevel


# info_logger.addFilter(LevelFilter(logging.INFO))
