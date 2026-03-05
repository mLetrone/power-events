"""Top-level Power event package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    # package is not installed
    __version__ = "undefined"

from .event import event_converter as event_converter
from .resolver import EventResolver as EventResolver
from .resolver import EventRouter as EventRouter
