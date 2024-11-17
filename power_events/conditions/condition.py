from abc import ABC, abstractmethod
from enum import Enum
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    TypeVar,
)

from typing_extensions import override

K = TypeVar("K")
V = TypeVar("V")
Event = Mapping[Any, V]


class Condition(ABC):
    """Abstract base class for a condition that can be checked against an event."""

    @abstractmethod
    def check(self, event: Event[V]) -> bool:
        """Check if the condition holds for the given event.

        Args:
            event: The event to check.
        """

    @abstractmethod
    def __or__(self, other: "Condition") -> "Condition":
        """Combine this condition with another condition using OR logic.

        Args:
            other: The other condition.
        """

    @abstractmethod
    def __and__(self, other: "Condition") -> "Condition":
        """Combine this condition with another condition using AND logic.

        Args:
            other: The other condition.
        """

    @abstractmethod
    def __invert__(self) -> "Condition":
        """Invert this condition (logical NOT)."""


class ConditionOperator(Enum):
    """Enum representing logical operators for condition combination."""

    AND = all
    OR = any

    def __call__(self, *condition: Iterable[Any]) -> bool:
        """Apply the logical operator to the given conditions.

        Args:
            condition: The conditions to combine.
        """
        operator: Callable[[Iterable[Any]], bool] = self.value
        return operator(*condition)


class ConditionExpression(Condition, ABC):
    """Abstract base class for a composite condition expression."""

    operator: ConditionOperator

    def __init__(self, *conditions: Condition) -> None:
        """Initialize the composite condition with the specified conditions.

        Args:
            conditions: The conditions that make up the expression.
        """
        self._conditions = conditions

    @override
    def check(self, event: Event[V]) -> bool:
        return self.operator(condition.check(event) for condition in self._conditions)

    @override
    def __and__(self, other: Condition) -> Condition:
        if not isinstance(other, Condition):
            return NotImplemented
        return And(self, other)

    @override
    def __or__(self, other: Condition) -> Condition:
        if not isinstance(other, Condition):
            return NotImplemented
        return Or(self, other)


class Or(ConditionExpression):
    """Composite condition representing the logical OR of its conditions."""

    operator = ConditionOperator.OR

    @override
    def __invert__(self) -> Condition:
        return And(*(~condition for condition in self._conditions))


class And(ConditionExpression):
    """Composite condition representing the logical AND of its conditions."""

    operator = ConditionOperator.AND

    @override
    def __invert__(self) -> Condition:
        return Or(*(~condition for condition in self._conditions))


def Neg(condition: Condition) -> Condition:
    """Create a new condition representing the logical NOT of the given condition.

    Args:
        condition: The condition to invert.
    """
    return ~condition
