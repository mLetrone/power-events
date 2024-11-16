from power_events.conditions.condition import (
    And,
    Or,
)
from power_events.conditions.value import Value


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

    def test_nested_or_conditions(self) -> None:
        condition = (Value("a.b").equals(1) & Value("a.c").equals("maypy")) | Value("d").is_truthy()

        assert condition.check({"a": {"b": 1, "c": "maypy"}, "d": False})
        assert condition.check({"a": {"b": 1, "c": "maypy"}, "d": True})
        assert condition.check({"a": {"b": 2, "c": "maypy"}, "d": True})
        assert not condition.check({"a": {"b": 2, "c": "maypy"}, "d": False})

    def test_nested_and_conditions(self) -> None:
        condition = (Value("a.b").equals(1) & Value("a.c").equals("maypy")) & Value("d").is_truthy()

        assert condition.check({"a": {"b": 1, "c": "maypy"}, "d": True})
        assert not condition.check({"a": {"b": 1, "c": "maypy"}, "d": False})
        assert not condition.check({"a": {"b": 2, "c": "maypy"}, "d": True})
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
