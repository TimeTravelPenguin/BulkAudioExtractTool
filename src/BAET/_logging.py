import inspect
import logging
from logging import LogRecord, Logger
from logging.handlers import QueueHandler, QueueListener
from queue import Queue
from uuid import uuid4

from rich.console import Console, ConsoleOptions, RenderResult
from rich.logging import RichHandler
from rich.table import Table

from BAET._console import log_console


rich_handler = RichHandler(rich_tracebacks=True, console=log_console)
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
    module_name = module.__name__

    logger = app_logger.getChild(module_name)
    return logger


class ConsoleLogDisplay:
    def __init__(self):
        self._enabled = False

        self.display = Table.grid()

        self.logger = app_logger.getChild(str(uuid4()))

        queue = Queue()
        queue_handler = QueueHandler(queue)
        handler = rich_handler  # logging.StreamHandler()

        self.listener = QueueListener(queue, handler)
        self.logger.addHandler(queue_handler)

    def __rich_console__(self, console: Console, options: ConsoleOptions) -> RenderResult:
        yield self.display

    def __del__(self):
        self.enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, enabled: bool):
        if self.enabled == enabled:
            return

        if enabled:
            self._start()
        else:
            self._stop()

        self._enabled = enabled

    def _start(self):
        if not self.enabled:
            self.listener.start()
        else:
            self.logger.warning("Logging listener is already running")

    def _stop(self):
        if self.enabled:
            self.listener.stop()
        else:
            self.logger.warning("Logging listener is not currently running")

    def _write_to_display(self, record: LogRecord):
        msg = record.getMessage()
        self.display.add_row(msg)
        return True

    def __enter__(self):
        self.listener.start()
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.listener.stop()


class LevelFilter(logging.Filter):
    def __init__(self, loglevel: int) -> None:
        super().__init__()
        self.loglevel = loglevel

    def filter(self, record):
        return record.levelno == self.loglevel


# info_logger.addFilter(LevelFilter(logging.INFO))