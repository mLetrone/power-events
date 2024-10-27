from typing import Any, Dict

import pytest

from power_events.condition import Value
from power_events.exceptions import NoRouteFoundError
from power_events.resolver import EventResolver


class TestResolver:
    def test_resolve_should_raise_no_route_when_set_to_disallow(self) -> None:
        app = EventResolver(allow_no_route=False)

        with pytest.raises(NoRouteFoundError):
            next(app.resolve({"a": 1}))

    def test_equal(self) -> None:
        app = EventResolver(allow_no_route=False)

        @app.equal("a.b", "TEST")
        def handle_test(_event: Dict[str, Any]) -> str:
            return "lol"

        res = app.resolve({"a": {"b": "TEST"}})

        assert list(res) == ["lol"]

    def test_resolve_multiple_routes(self) -> None:
        event = {"a": {"b": {"c": "TEST"}, "d": 1}}
        app = EventResolver(allow_multiple_routes=True)

        @app.when(Value("a.b.c").one_of(["TEST"]))
        def handle_test(_event: Dict[str, Any]) -> str:
            return "test"

        @app.equal("a.d", 1)
        def handle_d(_event: Dict[str, Any]) -> str:
            return "d"

        res = app.resolve(event)

        assert list(res) == ["test", "d"]
