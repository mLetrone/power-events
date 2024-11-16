import re
from typing import Any, Container, Mapping, Optional, Union, overload

from maypy import Mapper, Maybe, Predicate
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
from power_events.exceptions import NoPredicateError, ValueAbsentError

ValuePath = str
_KEY_PATH_REGEX = r"(\w+)+\.?"


class _MissingPredicate(Predicate[Any]):
    """A predicate that always returns False, representing a missing condition."""

    def __call__(self, val: Any) -> bool:
        raise NotImplementedError  # pragma: no cover

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
        self._value_mapper: Mapper[Any, Any] = mapper or (lambda val: val)

    @override
    def check(self, event: Event[V]) -> bool:
        """Check the given event respect the value condition.

        Raises:
            NoPredicateError: when no predicate has been set.
            ValueAbsentError: if a key define by the path is missing in event.
        """
        if self._predicate is MISSING:
            raise NoPredicateError(self.path)

        val = get_value_from_path(event, self.path)

        return self._predicate(Maybe.of(val).map(self._value_mapper).or_else(val))

    def is_truthy(self) -> Self:
        """Add value is truthy check to the condition."""
        return self.__add(is_truthy)

    def equals(self, expected: Any) -> Self:
        """Add value equals the expected value check to the condition.

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
        """Add value matches the given regex pattern check to the condition.

        Args:
            regex: regex to match (either a string or a Pattern)
            flags: regex flags; should bot be passed with a pattern.

        Raises:
            TypeError: when passing flags whereas a `Pattern` have been passed
        """
        return self.__add(match_regex(regex, flags))  # type: ignore[arg-type]

    def one_of(self, options: Container[Any]) -> Self:
        """Add value is one of the given options check to the condition.

        Args:
            options: The container of options.
        """
        return self.__add(one_of(options))

    def contains(self, *items: Any) -> Self:
        """Add value contains all the given items to the condition.

        Args:
            items: The items to check for.
        """
        return self.__add(contains(*items))

    def is_not_empty(self) -> Self:
        """Add value is not empty to the condition."""
        return self.__add(neg(is_empty))

    def is_length(self, length: int) -> Self:
        """Add value has the specified size to the condition.

        Args:
            length: The length expected.
        """
        return self.__add(is_length(length))

    def match(self, predicate: Predicate[Any]) -> Self:
        """Add value matches the given predicate to the condition.

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


def get_value_from_path(event: Event[V], path: ValuePath) -> Any:
    """Get the value at the given path from the event, if not present, raise an error`.

    Args:
        event: The event from which to retrieve the value.
        path: The path of the value in the event.

    Raises:
        ValueAbsentError: if a key define by the path is missing in event.
    """
    mapping: Union[Event[V], V] = dict(event)
    path_keys = re.findall(_KEY_PATH_REGEX, path)

    for key in path_keys:
        key_present = False

        if isinstance(mapping, Mapping):
            if key in mapping:
                mapping = mapping[key]
                key_present = True

        if not key_present:
            raise ValueAbsentError(path, key, event)
    return mapping
