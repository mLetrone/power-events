from typing import Any, List, Mapping


class PowerEventsError(Exception):
    """Base class for exceptions of power_events."""


class ValueAbsentError(PowerEventsError):
    """Exception raised when the value to check is not present inside the event."""

    def __init__(self, path: str, missing_key: str, event: Mapping[Any, Any]) -> None:
        self.path = path
        self.missing_key = missing_key
        super().__init__(
            f"The value define by path <{path}> is missing the key <{missing_key}> in event:\n{event}"
        )


class NoPredicateError(PowerEventsError):
    """Exception raised when no predicate has been set for a value condition."""

    def __init__(self, path: str) -> None:
        """Initialize the exception with the path that caused the error.

        Args:
            path: The path of the value condition.
        """
        super().__init__(f"No predicate has been set for the value condition on path {path}")


class RouteError(PowerEventsError):
    """Base class for exceptions related to routing errors."""


class NoRouteFoundError(RouteError):
    """Exception raised when no route is found for an event."""

    def __init__(self, event: Mapping[Any, Any], routes: List[str]) -> None:
        """Initialize the exception with the event and the registered routes.

        Args:
            event: The event that caused the error.
            routes: The list of registered route functions.
        """
        self.registered_routes = routes
        super().__init__(
            f"No route found for the current event: {event}.\n"
            f"Registered route functions are {', '.join(routes)}.\n"
            "If it's normal pass the option 'allow_no_route' at `False` in the resolver definition."
        )


class MultipleRoutesError(RouteError):
    """Exception raised when multiple routes are found for an event."""

    def __init__(self, event: Mapping[Any, Any], routes: List[str]) -> None:
        """Initialize the exception with the event and the available routes.

        Args:
            event: The event that caused the error.
            routes: The list of available route functions.
        """
        self.available_routes = routes
        super().__init__(
            f"Multiples routes found for the current event: {event}.\n"
            f"Available route functions are {', '.join(routes)}.\n"
            "If it's normal pass the option 'allow_multiple_routes' in the resolver definition."
        )
