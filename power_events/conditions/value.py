import re
from typing import Any, Container, Mapping, Optional, Union, overload

from maypy import Empty, Mapper, Maybe, Predicate
from maypy.predicates import (
    contains,
    equals,
    is_empty,
    is_length,
    is_truthy,
    match_regex,
    neg,
    one_of,
)
from typing_extensions import Self, override

from power_events.conditions.condition import And, Condition, Event, Or, V
from power_events.exceptions import NoPredicateError

ValuePath = str
_KEY_PATH_REGEX = r"(\w+)+\.?"


class _MissingPredicate(Predicate[Any]):
    """A predicate that always returns False, representing a missing condition."""

    def __call__(self, val: Any) -> bool:
        return False  # pragma: no cover

    def __repr__(self) -> str:
        return "Predicate<MISSING>"


MISSING = _MissingPredicate()


class Value(Condition):
    """Condition based on a value at a certain path in an event."""

    def __init__(self, value_path: ValuePath, mapper: Optional[Mapper[Any, Any]] = None) -> None:
        """Initialize the condition with the specified value path.

        Args:
            value_path: The path to the value in the event.
            mapper: mapper to transform value before checking predicates on it.
        """
        self.path = value_path
        self._predicate: Predicate[Any] = MISSING
        self._value_mapper = mapper or (lambda val: val)

    @override
    def check(self, event: Event[V]) -> bool:
        """Check if the condition holds for the given event.

        Raises:
            NoPredicateError: when no predicate has been set.
        """
        if self._predicate is MISSING:
            raise NoPredicateError(self.path)

        return (
            get_value_from_path(event, self.path)
            .map(self._value_mapper)
            .map(self._predicate)
            .or_else(False)
        )

    def is_truthy(self) -> Self:
        """Add the condition to check if the value is truthy."""
        return self.__add(is_truthy)

    def equals(self, expected: Any) -> Self:
        """Add the condition to check if the value equals the expected value.

        Args:
            expected: The expected value.
        """
        return self.__add(equals(expected))

    @overload
    def match_regex(self, regex: re.Pattern[str]) -> Self: ...

    @overload
    def match_regex(self, regex: str, flags: Union[re.RegexFlag, int] = 0) -> Self: ...

    def match_regex(
        self, regex: Union[re.Pattern[str], str], flags: Union[re.RegexFlag, int] = 0
    ) -> Self:
        """Add the condition to check if the value matches the given regex pattern.

        Args:
        regex: regex to match (either a string or a Pattern)
        flags: regex flags; should bot be passed with a pattern.

        Raises:
            TypeError: when passing flags whereas a `Pattern` have been passed
        """
        return self.__add(match_regex(regex, flags))  # type: ignore[arg-type]

    def one_of(self, options: Container[Any]) -> Self:
        """Add the condition to check if the value is one of the given options.

        Args:
            options: The container of options.
        """
        return self.__add(one_of(options))

    def contains(self, *items: Any) -> Self:
        """Add the condition to check if the value contains all the given items.

        Args:
            items: The items to check for.
        """
        return self.__add(contains(*items))

    def is_not_empty(self) -> Self:
        """Add the condition to check if the value is not empty."""
        return self.__add(neg(is_empty))

    def is_size(self, size: int) -> Self:
        """Add the condition to check if the value has the specified size.

        Args:
            size: The size to check for.
        """
        return self.__add(is_length(size))

    def match(self, predicate: Predicate[Any]) -> Self:
        """Add the condition to check if the value matches the given predicate.

        Args:
            predicate: The predicate to apply.
        """
        return self.__add(predicate)

    @override
    def __or__(self, other: Condition) -> Condition:
        if not isinstance(other, Condition):
            return NotImplemented
        return Or(self, other)

    @override
    def __and__(self, other: Condition) -> Condition:
        if not isinstance(other, Condition):
            return NotImplemented
        return And(self, other)

    @override
    def __invert__(self) -> Condition:
        invert = Value(self.path)
        invert._predicate = neg(self._predicate)
        return invert

    def __add(self, predicate: Predicate[Any]) -> Self:
        """Add new predicate to the current one.

        Args:
            predicate: The new predicate.
        """
        if self._predicate is MISSING:
            self._predicate = predicate
        else:
            self._predicate = combine(self._predicate, predicate)

        return self

    def __repr__(self) -> str:
        return f"Value(path={self.path}, predicate={self._predicate})"


def combine(*predicates: Predicate[Any]) -> Predicate[Any]:
    """Combine all provided predicates into a single predicate.

    Args:
        predicates: Predicates to combine.
    """

    def test(val: Any) -> bool:
        return all(predicate(val) for predicate in predicates)

    return test


def get_value_from_path(event: Event[V], path: ValuePath) -> Maybe[Any]:
    """Get the value at the given path from the event.

    Args:
        event: The event from which to retrieve the value.
        path: The path of the value in the event.
    """
    path_keys = re.findall(_KEY_PATH_REGEX, path)
    return deep_get(event, *path_keys)


def deep_get(event: Event[V], *keys: str) -> Maybe[Any]:
    """Recursively get the value from a nested mapping based on the given keys.

    Args:
        event: The event mapping.
        keys: The sequence of keys to follow.
    """
    mapping: Union[Event[V], V, None] = dict(event)

    for key in keys:
        if isinstance(mapping, Mapping):
            mapping = mapping.get(key)
        else:
            return Empty
    return Maybe.of(mapping)
