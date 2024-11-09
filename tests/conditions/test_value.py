from datetime import datetime

import pytest
from maypy.predicates import contains, is_length

from power_events.conditions import Neg, Value
from power_events.conditions.value import VALUE_ABSENT, combine, get_value_from_path
from power_events.exceptions import NoPredicateError


def test_combine() -> None:
    pred = combine(is_length(2), contains("maypy"))

    assert pred(["power-events", "maypy"])
    assert not pred(["mapy"])
    assert not pred([1, 2])


def test_get_value_from_path_should_return_empty_when_no_value() -> None:
    event = {"a": {"b": "c"}}

    assert get_value_from_path(event, "a.d") is VALUE_ABSENT


def test_get_value_from_path_should_return_value() -> None:
    event = {"a": {"b": "c"}}

    assert get_value_from_path(event, "a.b") == "c"


def test_get_value_from_path_with_empty_path_should_return_root() -> None:
    event = {"a": {"b": "c"}}
    assert get_value_from_path(event, "") == event


class TestValue:
    def test_is_truthy(self) -> None:
        assert Value("a.b").is_truthy().check({"a": {"b": True}})
        assert not Value("a.b").is_truthy().check({"a": 1})

    def test_equal_with_none(self) -> None:
        assert Value("a").equals(None).check({"a": None})

    def test_contains(self) -> None:
        assert Value("a.b").contains(1, 2).check({"a": {"b": [1, 2]}})

    def test_is_not_empty(self) -> None:
        assert Value("a.b").is_not_empty().check({"a": {"b": "not empty"}})
        assert not Value("a.b").is_not_empty().check({"a": {"b": []}})

    def test_is_size(self) -> None:
        assert Value("a.b").is_size(3).check({"a": {"b": [1, 2, 3]}})
        assert not Value("a.b").is_size(3).check({"a": {"b": []}})

    def test_one_of(self) -> None:
        assert Value("a.b").one_of(["foo", "bar"]).check({"a": {"b": "bar"}})
        assert not Value("a.b").one_of(["foo", "bar"]).check({"a": {"b": "baz"}})

    def test_match_regex(self) -> None:
        assert Value("a.b").match_regex(r"test_\d{2,}").check({"a": {"b": "test_123"}})
        assert not Value("a.b").match_regex(r"test_\d{2,}").check({"a": {"b": "test"}})

    def test_match(self) -> None:
        def is_even(val: int) -> bool:
            return val % 2 == 0

        assert Value("a.b").match(is_even).check({"a": {"b": 8}})
        assert not Value("a.b").match(is_even).check({"a": {"b": 7}})

    def test_check_false_when_value_not_in_event(self) -> None:
        assert not Value("a.b.c").equals(2).check({})

    def test_check_false_when_value_not_equals(self) -> None:
        assert not Value("a.b.c").equals(2).check({"a": {"b": {"c": 1}}})

    def test_check_value(self) -> None:
        assert Value("a.b").equals(2).check({"a": {"b": 2}})

    def test_invert(self) -> None:
        value = Value("a.b").equals(2)

        assert ~value.check({"a": {"b": 1}})
        assert Neg(value).check({"a": {"b": 1}})

    def test_check_should_raise_error_when_no_predicate_set(self) -> None:
        with pytest.raises(NoPredicateError):
            Value("a.b.c").check({})

    def test_check_multiple_predicates(self) -> None:
        value = Value("a").contains(1).is_size(3)
        assert value.check({"a": [3, 2, 1]})
        assert not value.check({"a": [3, 1]})
        assert not value.check({"a": [3, 2, 4]})

    def test_mapper(self) -> None:
        value = Value("a").match(lambda val: val < datetime.now())

        with pytest.raises(TypeError):
            value.check({"a": "2021-02-08"})

        value._value_mapper = lambda val: datetime.strptime(val, "%Y-%m-%d")

        assert value.check({"a": "2021-02-08"})
