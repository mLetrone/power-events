import pytest
from maypy import Maybe
from maypy.predicates import contains, is_length

from src.power_events.condition import (
    And,
    Or,
    Value,
    combine,
    get_value_from_path,
)
from src.power_events.exceptions import NoPredicateError


def test_combine() -> None:
    pred = combine(is_length(2), contains("maypy"))

    assert pred(["power-events", "maypy"])
    assert not pred(["mapy"])
    assert not pred([1, 2])


def test_get_value_from_path_should_return_empty_when_no_value() -> None:
    event = {"a": {"b": "c"}}

    assert get_value_from_path(event, "a.d").is_empty()


def test_get_value_from_path_should_return_value() -> None:
    event = {"a": {"b": "c"}}

    assert get_value_from_path(event, "a.b") == Maybe.of("c")


class TestValue:
    def test_check_false_when_value_not_in_event(self) -> None:
        assert not Value("a.b.c").equals(2).check({})

    def test_check_false_when_value_not_equals(self) -> None:
        assert not Value("a.b.c").equals(2).check({"a": {"b": {"c": 1}}})

    def test_check_value(self) -> None:
        assert Value("a.b").equals(2).check({"a": {"b": 2}})

    def test_invert(self) -> None:
        value = Value("a.b").equals(2)

        assert ~value.check({"a": {"b": 1}})

    def test_check_should_raise_error_when_no_predicate_set(self) -> None:
        with pytest.raises(NoPredicateError):
            Value("a.b.c").check({})


class TestCondition:
    def test_condition_or(self) -> None:
        condition = Value("a.b").equals(1) | Value("a.c").equals("maypy")

        assert condition.check({"a": {"b": 0, "c": "maypy"}})

    def test_condition_or_no_match(self) -> None:
        condition = Value("a.b").equals(1) | Value("a.c").equals("maypy")

        assert not condition.check({"a": {"b": 0, "c": 1}})

    def test_condition_and(self) -> None:
        condition = Value("a.b").equals(1) & Value("a.c").equals("maypy")

        assert condition.check({"a": {"b": 1, "c": "maypy"}})

    def test_condition_and_no_match(self) -> None:
        condition = Value("a.b").equals(1) & Value("a.c").equals("maypy")

        assert not condition.check({"a": {"b": 1, "c": 2}})

    def test_nested_conditions(self) -> None:
        condition = (Value("a.b").equals(1) & Value("a.c").equals("maypy")) | Value("d").is_truthy()

        assert condition.check({"a": {"b": 1, "c": "maypy"}})
        assert condition.check({"d": True})
        assert condition.check({"a": {"b": 1, "c": "maypy"}, "d": True})
        assert condition.check({"a": {"b": 2, "c": "maypy"}, "d": True})
        assert not condition.check({"a": {"b": 2, "c": "maypy"}, "d": False})

    def test_invert_or_condition(self) -> None:
        condition = ~(Value("a.b").equals(1) | Value("a.c").equals("maypy"))

        assert isinstance(condition, And)

        assert condition.check({"a": {"b": 0, "c": 1}})
        assert not condition.check({"a": {"b": 1, "c": 1}})
        assert not condition.check({"a": {"b": 0, "c": "maypy"}})
        assert not condition.check({"a": {"b": 1, "c": "maypy"}})

    def test_invert_and_condition(self) -> None:
        condition = ~(Value("a.b").equals(1) & Value("a.c").equals("maypy"))

        assert isinstance(condition, Or)

        assert condition.check({"a": {"b": 0, "c": "maypy"}})
        assert condition.check({"a": {"b": 1, "c": "power-events"}})
        assert not condition.check({"a": {"b": 1, "c": "maypy"}})
