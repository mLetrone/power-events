from datetime import datetime
from typing import List, Optional

import pytest
from maypy.predicates import contains, is_length

from power_events.conditions import Neg
from power_events.conditions.value import ABSENT, Value, ValuePath, combine
from power_events.exceptions import NoPredicateError, ValueAbsentError


def test_combine() -> None:
    pred = combine(is_length(2), contains("maypy"))

    assert pred(["power-events", "maypy"])
    assert not pred(["mapy"])
    assert not pred([1, 2])


class TestValuePath:
    def test_should_raise_error_when_path_begin_by_sep(self) -> None:
        with pytest.raises(ValueError, match="Path value should not begin"):
            ValuePath(".a.b")

    def test_should_raise_error_when_path_end_by_sep(self) -> None:
        with pytest.raises(ValueError, match="Path value should not end"):
            ValuePath("a.b.")

    def test_should_raise_error_when_path_has_consecutive_sep(self) -> None:
        with pytest.raises(ValueError, match="Path value should not contain consecutive"):
            ValuePath("a..b")

    @pytest.mark.parametrize(
        ("path", "sep", "keys"),
        [
            ("", None, []),
            ("effective-date/1", "/", ["effective-date", "1"]),
            ("effective+date+1", "+", ["effective", "date", "1"]),
        ],
    )
    def test_should_create_when_valid_path(
        self, path: str, sep: Optional[str], keys: List[str]
    ) -> None:
        assert ValuePath(path, separator=sep).keys == keys

    def test_get_when_path_empty_should_return_event(self) -> None:
        assert ValuePath("").get({"a": 1}) == {"a": 1}

    def test_get_should_return_value(self) -> None:
        assert ValuePath("a.b").get_from({"a": {"b": 2}}) == 2

    def test_get_should_handle_int_key(self) -> None:
        assert ValuePath("a.b.1").get_from({"a": {"b": {1: "int"}}}) == "int"
        assert ValuePath("a.b.1").get_from({"a": {"b": {"1": "str"}}}) == "str"

    def test_get_should_return_absent_sentinel_by_default_when_no_value_at_path(self) -> None:
        assert ValuePath("a.b").get_from({"a": {"c": 2}}) is ABSENT

    def test_get_should_return_default_value_when_given_and_value_absent(self) -> None:
        path = ValuePath("a.b")
        assert path.get_from({}, None) is None
        assert path.get_from({"a": 1}, None) is None

    def test_get_should_raise_error_when_no_value_and_flag_set(self) -> None:
        with pytest.raises(ValueAbsentError) as excinfo:
            ValuePath("foo.bar").get_from({"foo": {}}, raise_if_absent=True)
            assert excinfo.value.missing_key == "bar"
            assert excinfo.value.path == "foo.bar"


class TestValue:
    def test_root(self) -> None:
        assert Value.root().contains("a").check({"a": 1})

    def test_is_truthy(self) -> None:
        assert Value("a.b").is_truthy().check({"a": {"b": True}})
        assert not Value("a.b").is_truthy().check({"a": {"b": False}})

    def test_equal_with_none(self) -> None:
        assert Value("a").equals(None).check({"a": None})

    def test_contains(self) -> None:
        assert Value("a.b").contains(1, 2).check({"a": {"b": [1, 2]}})

    def test_is_not_empty(self) -> None:
        assert Value("a.b").is_not_empty().check({"a": {"b": "not empty"}})
        assert not Value("a.b").is_not_empty().check({"a": {"b": []}})

    def test_is_size(self) -> None:
        assert Value("a.b").is_length(3).check({"a": {"b": [1, 2, 3]}})
        assert not Value("a.b").is_length(3).check({"a": {"b": []}})

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

    def test_equals(self) -> None:
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

    def test_check_raise_error_when_value_not_in_event_and_flag_raise(self) -> None:
        with pytest.raises(ValueAbsentError):
            Value("a.b.c").equals(2).check({}, raise_if_absent=True)

    def test_check_should_return_false_when_value_absent(self) -> None:
        assert not Value("a.b.c").equals(2).check({})

    def test_check_multiple_predicates(self) -> None:
        value = Value("a").contains(1).is_length(3)
        assert value.check({"a": [3, 2, 1]})
        assert not value.check({"a": [3, 1]})
        assert not value.check({"a": [3, 2, 4]})

    def test_mapper(self) -> None:
        value = Value("a").match(lambda val: val < datetime.now())

        with pytest.raises(TypeError):
            value.check({"a": "2021-02-08"})

        value.mapper = lambda val: datetime.strptime(val, "%Y-%m-%d")

        assert value.check({"a": "2021-02-08"})
