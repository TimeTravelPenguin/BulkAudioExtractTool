import inspect
import logging
from collections.abc import Callable
from functools import wraps
from logging import FileHandler, Logger
from pathlib import Path
from types import ModuleType
from typing import Any

from rich.logging import RichHandler

from .console import app_console

rich_handler = RichHandler(rich_tracebacks=True, console=app_console)
logging.basicConfig(
    level=logging.INFO,
    format="%(threadName)s: %(message)s",
    datefmt="[%X]",
    handlers=[rich_handler],
)

app_logger = logging.getLogger("app_logger")


def pass_module(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator that passes the module name to the decorated function."""
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return func(module, *args, **kwargs)

    return wrapper


@pass_module
def create_logger(module: ModuleType) -> Logger:
    """Create and return a logger for the current module."""
    if module is None:
        raise RuntimeError("Could not inspect module")

    module_name = module.__name__

    logger = app_logger.getChild(module_name)
    return logger


@pass_module
def find_module_logger(module: ModuleType) -> Logger:
    """Find the logger for the current module.

    Parameters
    ----------
    module : ModuleType
        The module to find the logger for.

    Returns
    -------
    Logger | None
        The logger for the module, or None if it doesn't exist.

    Raises
    ------
    TypeError
        If the found logger variable is not of type logging.Logger.
    """
    logger = getattr(module, "logger", app_logger)

    if not isinstance(logger, logging.Logger):
        raise TypeError("logger must be of type logging.Logger")

    return logger


def pass_logger(func: Callable[..., Any]) -> Callable[..., Any]:
    """Passes the modules logger to the decorated function, if it exists. Otherwise, uses the root logger.

    Parameters
    ----------
    func : Callable[..., Any]
        The function to decorate.

    Returns
    -------
    Callable[..., Any]
        The newly decorated function.

    Raises
    ------
    RuntimeError
        If the module cannot be inspected.
    """

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger = find_module_logger()

        if logger is None:
            logger = app_logger

        return func(logger, *args, **kwargs)

    return wrapper


def configure_logging(*, enable_logging: bool = True, file_out: Path | None = None) -> None:
    """Configure logging.

    Parameters
    ----------
    enable_logging : bool, optional
        Whether to enable logging, by default True
    file_out : Path | None, optional
        The file to write logs to, by default None
    """
    if not enable_logging:
        logging.disable(logging.INFO)

    if file_out is not None:
        handler = FileHandler(filename=file_out)
        handler.setFormatter(rich_handler.formatter)
        app_logger.addHandler(handler)
