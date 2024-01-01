import inspect
import logging
from logging import Logger

from rich.logging import RichHandler

from BAET._console import app_console

rich_handler = RichHandler(rich_tracebacks=True, console=app_console)
logging.basicConfig(
    level=logging.INFO,
    format="%(threadName)s: %(message)s",
    datefmt="[%X]",
    handlers=[rich_handler],
)

app_logger = logging.getLogger("app_logger")


def create_logger() -> Logger:
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])

    if module is None:
        raise RuntimeError("Could not inspect module")

    module_name = module.__name__

    logger = app_logger.getChild(module_name)
    return logger
