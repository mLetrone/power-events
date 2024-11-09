from collections.abc import Mapping
from typing import Any, Dict

import pytest

from power_events.conditions.value import Value
from power_events.exceptions import MultipleRoutesError, NoRouteFoundError
from power_events.resolver import EventResolver, EventRoute


class TestEventRoute:
    def test_match(self) -> None:
        def route(event: Any) -> int:
            return 1

        assert EventRoute(route, Value("a").equals(1)).match({"a": 1})

    def test_name(self) -> None:
        def route_test_name(event: Any) -> int:
            return 1

        assert EventRoute(route_test_name, Value("a").equals(1)).name == "route_test_name"
        assert EventRoute(lambda x: x, Value("a").equals(1)).name == "<lambda>"


class TestResolver:
    def test_resolve_should_raise_no_route_when_set_to_disallow(self) -> None:
        app = EventResolver(allow_no_route=False)

        with pytest.raises(NoRouteFoundError):
            app.resolve({"a": 1})

    def test_resolve_should_raise_multiple_route_when_set_to_disallow(self) -> None:
        app = EventResolver(allow_multiple_routes=False)

        @app.equal("a.b", "TEST")
        def handle_test(_event: Mapping[str, Any]) -> str:
            return "lol"

        @app.equal("a.b", "TEST")
        def handle_test2(_event: Dict[str, Any]) -> str:
            return "lol-2"

        with pytest.raises(MultipleRoutesError):
            app.resolve({"a": {"b": "TEST"}})

    def test_equal(self) -> None:
        app = EventResolver(allow_no_route=False)

        @app.equal("a.b", "TEST")
        def handle_test(_event: Dict[str, Any]) -> str:
            return "lol"

        res = app.resolve({"a": {"b": "TEST"}})

        assert res == ["lol"]

    def test_one_of(self) -> None:
        app = EventResolver()

        @app.one_of("a", ["BAR", "FOO"])
        def handle_foo(_event: Dict[str, Any]) -> str:
            return "BAR"

        res = app.resolve({"a": "FOO"})

        assert res == ["BAR"]

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

        assert res == ["test", "d"]
