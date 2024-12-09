import re
from typing import Any, Container, List, Mapping, Optional, Union, overload

from maypy import Mapper, Maybe, Predicate
from maypy.predicates import (
    contains,
    equals,
    is_blank_str,
    is_empty,
    is_length,
    is_truthy,
    match_regex,
    neg,
    one_of,
)
from typing_extensions import Self, deprecated, override

from power_events.conditions.condition import And, Condition, Event, Or, V
from power_events.exceptions import NoPredicateError, ValueAbsentError


class Absent:
    """Sentinel class to represent value absence."""


ABSENT = Absent()


class ValuePath(str):
    """A path-like string for accessing nested mappings value."""

    SEPARATOR = "."
    separator: str
    keys: List[str]

    def __new__(cls, path: str, *, separator: Optional[str] = None) -> Self:
        """Create a new ValuePath object from a path string.

        Args:
            path: path string of a value inside a mapping object.
            separator: custom separator to use instead of the default.
        """
        separator = separator or cls.SEPARATOR
        is_blank = is_blank_str(path)

        if not is_blank:
            cls._validation(path, separator)

        instance = super().__new__(cls, path)
        instance.separator = separator
        instance.keys = [] if is_blank else instance.strip().split(separator)

        return instance

    def get_from(
        self,
        mapping: Mapping[Any, V],
        default: Union[V, None, Absent] = ABSENT,
        *,
        raise_if_absent: bool = False,
    ) -> Union[Any, None, Absent]:
        """Get the value describe by the path inside mapping object.

        The value returns can be the sentinel `ABSENT` to differentiate real `None` value of default.

        Args:
            mapping: Dictionary or mapping object to lookup.
            default: Default value if key not found. By default return the sentinel value `ABSENT`.
            raise_if_absent: Flag to raise `ValueAbsentError` if missing key. Default `False`

        Note:
            Support both string and integer keys.

        Raises:
            ValueAbsentError: if parameter `raise_if_absent` set, and key is missing.
        """
        value: Union[Mapping[Any, V], V, None, Absent] = dict(mapping)
        for key in self.keys:
            key_present = False

            if isinstance(value, Mapping):
                if key in value:
                    value = value[key]
                    key_present = True

                elif key.isdigit() and (num_key := int(key)) in value:
                    value = value[num_key]
                    key_present = True

            if not key_present:
                if raise_if_absent:
                    raise ValueAbsentError(self, key, mapping)
                return default
        return value

    @deprecated("""
    `get` is deprecated, use `get_from` instead.
    """)
    def get(
        self,
        mapping: Mapping[Any, V],
        default: Union[V, None, Absent] = ABSENT,
        *,
        raise_if_absent: bool = False,
    ) -> Union[Any, None, Absent]:
        """Get the value describe by the path inside mapping object.

        `get` is deprecated, use `get_from` instead.

        The value returns can be the sentinel `ABSENT` to differentiate real `None` value of default.

        Args:
            mapping: Dictionary or mapping object to lookup.
            default: Default value if key not found. By default return the sentinel value `ABSENT`.
            raise_if_absent: Flag to raise `ValueAbsentError` if missing key. Default `False`

        Note:
            Support both string and integer keys.

        Raises:
            ValueAbsentError: if parameter `raise_if_absent` set, and key is missing.
        """
        return self.get_from(mapping, default, raise_if_absent=raise_if_absent)

    @staticmethod
    def _validation(path: str, sep: str) -> None:
        """Validate string path."""
        if path[0] == sep:
            raise ValueError(f"Path value should not begin by key sep '{sep}'")

        if path[-1] == sep:
            raise ValueError(f"Path value should not end by key sep '{sep}'")

        if sep * 2 in path:
            raise ValueError(
                f"Path value should not contain consecutive separators, '{sep * 2}' is forbidden"
            )


class _MissingPredicate(Predicate[Any]):
    """A predicate that always returns False, representing a missing condition."""

    def __call__(self, val: Any) -> bool:
        raise NotImplementedError  # pragma: no cover

    def __repr__(self) -> str:
        return "Predicate<MISSING>"


MISSING = _MissingPredicate()


class Value(Condition):
    """Condition based on a value at a certain path in an event."""

    def __init__(self, value_path: str, mapper: Optional[Mapper[Any, Any]] = None) -> None:
        """Initialize the condition with the specified value path.

        Args:
            value_path: The path to the value in the event.
            mapper: mapper to transform value before checking predicates on it.
        """
        self.path: ValuePath = ValuePath(value_path)
        self._predicate: Predicate[Any] = MISSING
        self.mapper: Mapper[Any, Any] = mapper or (lambda val: val)

    @classmethod
    def root(cls) -> Self:
        """Initialize value targeting condition over the event itself.

        Examples:
            ```python
            Value.root().contains("a").check(my_dict)
            #  is equivalent to.
            "a" in my_dict
            ```
        """
        return cls("")

    @override
    def check(self, event: Event[V], *, raise_if_absent: bool = False) -> bool:
        """Check the given event respect the value condition.

        By default, the event fails the check if the value is absent, an error can be raised,
        by setting the flag `raise_if_absent`.

        Raises:
            NoPredicateError: when no predicate has been set.
            ValueAbsentError: if a key define by the path is missing in event.
        """
        if self._predicate is MISSING:
            raise NoPredicateError(self.path)

        if (val := self.path.get_from(event, raise_if_absent=raise_if_absent)) is ABSENT:
            return False

        return self._predicate(Maybe.of(val).map(self.mapper).or_else(val))

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
