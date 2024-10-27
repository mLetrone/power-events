from dataclasses import dataclass
from logging import Logger
from typing import (
    Any,
    Callable,
    Container,
    Iterator,
    List,
    Mapping,
    TypedDict,
    TypeVar,
)

from maypy.predicates import is_empty
from typing_extensions import Unpack

from .condition import Condition, Value, ValuePath
from .exceptions import MultipleRoutesError, NoRouteFoundError

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")

Func = TypeVar("Func", bound=Callable[..., Any])

logger = Logger("power_events")


class Options(TypedDict, total=False):
    allow_multiple_routes: bool
    allow_no_route: bool


@dataclass
class EventRoute:
    """Class representing an event route with a condition and a function."""

    func: Callable[..., Any]
    condition: Condition

    def is_match(self, event: Mapping[str, V]) -> bool:
        """Check if the event matches the route's condition.

        Args:
            event: The event to check.
        """
        return self.condition.check(event)

    @property
    def name(self) -> str:
        """Get the name of the route function."""
        return self.func.__name__


class EventResolver:
    """Class responsible for resolving events against registered routes."""

    def __init__(self, **options: Unpack[Options]) -> None:
        """Initialize the event resolver with optional configuration.

        Args:
            **options: The optional configuration settings.
        """
        self._routes: List[EventRoute] = []
        self._allow_multiple_routes = options.get("allow_multiple_routes", False)
        self._allow_no_route = options.get("allow_no_route", True)

    def equal(self, value_path: ValuePath, expected: Any) -> Callable[[Func], Func]:
        """Register a route with an equality condition.

        Args:
            value_path: The path to the value in the event.
            expected: The expected value.
        """
        return self.when(Value(value_path).equals(expected))

    def one_of(self, value_path: ValuePath, options: Container[Any]) -> Callable[[Func], Func]:
        """Register a route with a one-of condition.

        Args:
            value_path: The path to the value in the event.
            options: The container of expected values.
        """
        return self.when(Value(value_path).one_of(options))

    def when(self, condition: Condition) -> Callable[[Func], Func]:
        """Register a route with a custom condition.

        Args:
            condition: The condition to apply to the route.
        """

        def register_route(fn: Func) -> Func:
            route = EventRoute(condition=condition, func=fn)
            self._routes.append(route)
            return fn

        return register_route

    def resolve(self, event: Mapping[str, V]) -> Iterator[Any]:
        """Resolve the event to the matching routes and execute their functions.

        Args:
            event: The event to resolve.
        """
        available_routes = [route for route in self._routes if route.is_match(event)]
        self._handle_not_found(event, available_routes)
        self._handle_multiple_routes(event, available_routes)

        for route in available_routes:
            yield route.func(event)

    def _handle_multiple_routes(
        self, event: Mapping[str, V], available_routes: List[EventRoute]
    ) -> None:
        """Handle cases where multiple routes match the event.

        Args:
            event: The event to resolve.
            available_routes: The list of matching routes.

        Raises:
            MultipleRoutesError: If multiple routes are found and not allowed.
        """
        if len(available_routes) > 1:
            if not self._allow_multiple_routes:
                raise MultipleRoutesError(event, [route.name for route in available_routes])
            logger.warning("Multiple routes for this event")

    def _handle_not_found(self, event: Mapping[str, V], available_routes: List[EventRoute]) -> None:
        """Handle cases where no routes match the event.

        Args:
            event: The event to resolve.
            available_routes: The list of matching routes.

        Raises:
            NoRouteFoundError: If no routes are found and not allowed.
        """
        if is_empty(available_routes):
            if not self._allow_no_route:
                raise NoRouteFoundError(event, [route.name for route in self._routes])
            logger.warning("No routes for this event")
