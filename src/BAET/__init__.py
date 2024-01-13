from importlib.metadata import version

from ._config.console import app_console
from ._config.logging import configure_logging, create_logger
from .theme import app_theme

__version__ = version(__name__)

__all__ = ["app_console", "configure_logging", "create_logger", "app_theme"]
