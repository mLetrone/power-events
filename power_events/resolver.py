from collections.abc import Sequence
from dataclasses import dataclass
from logging import Logger
from typing import (
    Any,
    Callable,
    Container,
    Dict,
    List,
    Mapping,
    Optional,
    Type,
    TypeVar,
    Union,
    overload,
)

from maypy.predicates import is_empty
from typing_extensions import Concatenate, ParamSpec

from .conditions import Condition, Value
from .exceptions import MultipleRoutesError, NoRouteFoundError

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")
Error = TypeVar("Error", bound=Exception)
P = ParamSpec("P")

Func = Callable[Concatenate[Dict[Any, Any], P], Any]

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
            allow_multiple_routes: option to allow multiples routes on same event, otherwise raise `MultipleRoutesError`.
            allow_no_route: option to allow no routes on event, otherwise raise `NoRouteFoundError`.
        """
        self._routes: List[EventRoute] = []
        self._fallback_route: Optional[EventRoute] = None
        self._exception_handlers: Dict[Type[Exception], Callable[..., Any]] = {}
        self._allow_multiple_routes = allow_multiple_routes
        self._allow_no_route = allow_no_route

    def equal(self, value_path: str, expected: Any) -> Callable[[Func[P]], Func[P]]:
        """Register a route with an equality condition.

        Args:
            value_path: The path to the value in the event.
            expected: The expected value.
        """
        return self.when(Value(value_path).equals(expected))

    def one_of(self, value_path: str, options: Container[V]) -> Callable[[Func[P]], Func[P]]:
        """Register a route with a one-of condition.

        Args:
            value_path: The path to the value in the event.
            options: The container of expected values.
        """
        return self.when(Value(value_path).one_of(options))

    def contain(self, value_path: str, *items: V) -> Callable[[Func[P]], Func[P]]:
        """Register a route where value should contain items.

        Args:
            value_path: The path to the value in the event.
            items: Items to in the event.
        """
        return self.when(Value(value_path).contains(*items))

    def when(self, condition: Condition) -> Callable[[Func[P]], Func[P]]:
        """Register a route with a custom condition.

        Args:
            condition: The condition to trigger this route.
        """

        def register_route(fn: Func[P]) -> Func[P]:
            route = EventRoute(condition=condition, func=fn)
            self._routes.append(route)
            return fn

        return register_route

    @overload
    def exception_handler(
        self, exc_type: Type[Error]
    ) -> Callable[[Callable[[Error], Any]], Callable[[Error], Any]]: ...

    @overload
    def exception_handler(
        self, exc_type: Sequence[Type[Exception]]
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]: ...

    def exception_handler(
        self, exc_type: Union[Type[Error], Sequence[Type[Error]]]
    ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Register a function to handle certain exception type.

        Parameters:
            exc_type: exception type to handle.
                Could be either a unique exception type or a list of types.
        """

        def register_exception(fn: Callable[..., Any]) -> Callable[..., Any]:
            if isinstance(exc_type, Sequence):
                for exc in exc_type:
                    self._exception_handlers[exc] = fn
            else:
                self._exception_handlers[exc_type] = fn
            return fn

        return register_exception

    @overload
    def fallback(self) -> Callable[[Func[P]], Func[P]]: ...

    @overload
    def fallback(self, func: Func[P]) -> Func[P]: ...

    def fallback(
        self, func: Optional[Func[P]] = None
    ) -> Union[Callable[[Func[P]], Func[P]], Func[P]]:
        """Register a fallback route if no registered routes match the event."""

        def register_fallback(fn: Func[P]) -> Func[P]:
            self._fallback_route = EventRoute(fn, Value.root().match(lambda x: True))
            return fn

        if func is None:
            return register_fallback  # pragma: no cover

        return register_fallback(func)

    def resolve(self, event: Mapping[Any, V]) -> Sequence[Any]:
        """Resolve the event to the matching routes and execute their functions.

        Args:
            event: The event to resolve.
        """
        available_routes = self._find_matching_routes(event)
        try:
            self._handle_not_found(event, available_routes)
            self._handle_multiple_routes(event, available_routes)

            return [route.func(event) for route in available_routes]

        except Exception as exc:
            handler = self._lookup_exception_handler(exc)
            if handler:
                return [handler(exc)]

            raise

    def _find_matching_routes(self, event: Mapping[Any, V]) -> List[EventRoute]:
        """Find the routes matching the event."""
        matching_routes = [route for route in self._routes if route.match(event)]

        if is_empty(matching_routes) and self._fallback_route:
            logger.debug("Use fallback route.")
            return [self._fallback_route]

        return matching_routes

    def _handle_not_found(self, event: Mapping[Any, V], available_routes: List[EventRoute]) -> None:
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

    def _handle_multiple_routes(
        self, event: Mapping[Any, V], available_routes: List[EventRoute]
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

    def _lookup_exception_handler(self, exc: Exception) -> Optional[Callable[[Exception], Any]]:
        """Lookup the handler for the exception using Method Resolution Order, for matching against base exception."""
        for cls in type(exc).__mro__:
            if cls in self._exception_handlers:
                return self._exception_handlers[cls]

        return None
