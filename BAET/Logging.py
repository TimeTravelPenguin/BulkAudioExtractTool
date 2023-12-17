import logging

from rich.logging import RichHandler

__ALL__ = ["info_logger"]

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)],
)

info_logger = logging.getLogger("info_logger")


class LevelFilter(logging.Filter):
    def __init__(self, loglevel: int) -> None:
        super().__init__()
        self.loglevel = loglevel

    def filter(self, record):
        return record.levelno == self.loglevel


info_logger.addFilter(LevelFilter(logging.INFO))
