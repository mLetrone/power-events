from collections.abc import Mapping
from functools import wraps
from typing import Any, Callable, Concatenate, TypeVar

from typing_extensions import ParamSpec

Event = TypeVar("Event", bound=Mapping[str, Any])
OUT = TypeVar("OUT")
P = ParamSpec("P")
R = TypeVar("R")
Func = Callable[Concatenate[OUT, P], R]


def event_converter(
    converter: Callable[[Event], OUT],
) -> Callable[[Callable[Concatenate[OUT, P], R]], Callable[Concatenate[OUT, P], R]]:
    """Decorator that converts the raw event and inject it to the decorated function.

    Args:
        converter: The converter function that transform the raw event to the desired output.

    Returns:
        The decorated function.
    """

    def decorator(func: Callable[Concatenate[OUT, P], R]) -> Callable[Concatenate[OUT, P], R]:
        @wraps(func)
        def wrapper(event: Any, /, *args: P.args, **kwargs: P.kwargs) -> R:
            return func(converter(event), *args, **kwargs)

        return wrapper

    return decorator
