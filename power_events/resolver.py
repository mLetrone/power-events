from collections.abc import Sequence
from dataclasses import dataclass
from logging import Logger
from typing import Any, Callable, Container, Dict, List, Mapping, TypeVar

from maypy.predicates import is_empty
from typing_extensions import Concatenate, ParamSpec

from .conditions import Condition, Value, ValuePath
from .exceptions import MultipleRoutesError, NoRouteFoundError

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
P = ParamSpec("P")

Func = Callable[Concatenate[Dict[str, Any], P], Any]

logger = Logger("power_events")


@dataclass(frozen=True)
class EventRoute:
    """Class representing an event route with a condition and a function."""

    func: Callable[..., Any]
    condition: Condition

    def match(self, event: Mapping[str, V]) -> bool:
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

    def __init__(self, allow_multiple_routes: bool = False, allow_no_route: bool = True) -> None:
        """Initialize the event resolver with optional configuration.

        Args:
            allow_multiple_routes: option to allow multiples routes on same event, otherwaise raise `MultipleRoutesError`.
            allow_no_route: option to allow no routes on event, otherwaise raise `NoRouteFoundError`.
        """
        self._routes: List[EventRoute] = []
        self._allow_multiple_routes = allow_multiple_routes
        self._allow_no_route = allow_no_route

    def equal(self, value_path: ValuePath, expected: Any) -> Callable[[Func[P]], Func[P]]:
        """Register a route with an equality condition.

        Args:
            value_path: The path to the value in the event.
            expected: The expected value.
        """
        return self.when(Value(value_path).equals(expected))

    def one_of(
        self, value_path: ValuePath, options: Container[Any]
    ) -> Callable[[Func[P]], Func[P]]:
        """Register a route with a one-of condition.

        Args:
            value_path: The path to the value in the event.
            options: The container of expected values.
        """
        return self.when(Value(value_path).one_of(options))

    def when(self, condition: Condition) -> Callable[[Func[P]], Func[P]]:
        """Register a route with a custom condition.

        Args:
            condition: The condition to apply to the route.
        """

        def register_route(fn: Func[P]) -> Func[P]:
            route = EventRoute(condition=condition, func=fn)
            self._routes.append(route)
            return fn

        return register_route

    def resolve(self, event: Mapping[str, V]) -> Sequence[Any]:
        """Resolve the event to the matching routes and execute their functions.

        Args:
            event: The event to resolve.
        """
        available_routes = [route for route in self._routes if route.match(event)]
        self._handle_not_found(event, available_routes)
        self._handle_multiple_routes(event, available_routes)

        return [route.func(event) for route in available_routes]

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
            logger.warning("Multiple routes for this event")  # pragma: no cover

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
            logger.warning("No routes for this event")  # pragma: no cover
