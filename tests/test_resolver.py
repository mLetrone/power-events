from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal

import pytest

from power_events.conditions import Neg, Value
from power_events.event import event_converter
from power_events.exceptions import MultipleRoutesError, NoRouteFoundError
from power_events.resolver import EventResolver, EventRoute, EventRouter


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

    def test_resolve_should_do_nothing_when_no_route(self) -> None:
        app = EventResolver()

        @app.equal("a.b", "TEST")
        def handle_test(_event: Mapping[str, Any]) -> str:
            return "lol"

        assert app.resolve({"a": 1}) == []

    def test_resolve_should_use_fallback_route_when_no_route_match(self) -> None:
        app = EventResolver()

        @app.equal("a.b", "TEST")
        def handle_test(_event: Mapping[str, Any]) -> str:
            return "lol"

        @app.fallback
        def fallback(_event: dict[str, str]) -> str:
            return "fallback"

        assert app.resolve({"a": 1}) == ["fallback"]

    def test_resolve_should_raise_multiple_route_when_set_to_disallow(self) -> None:
        app = EventResolver(allow_multiple_routes=False)

        @app.equal("a.b", "TEST")
        def handle_test(_event: Mapping[str, Any]) -> str:
            return "lol"

        @app.equal("a.b", "TEST")
        def handle_test2(_event: dict[str, Any]) -> str:
            return "lol-2"

        with pytest.raises(MultipleRoutesError):
            app.resolve({"a": {"b": "TEST"}})

    def test_equal(self) -> None:
        app = EventResolver(allow_no_route=False)

        @app.equal("a.b", "TEST")
        def handle_test(_event: dict[str, Any]) -> str:
            return "lol"

        res = app.resolve({"a": {"b": "TEST"}})

        assert res == ["lol"]

    def test_one_of(self) -> None:
        app = EventResolver()

        @app.one_of("a", ["BAR", "FOO"])
        def handle_foo(_event: dict[str, Any]) -> str:
            return "BAR"

        res = app.resolve({"a": "FOO"})

        assert res == ["BAR"]

    def test_contain(self) -> None:
        app = EventResolver()

        @app.one_of("a", ["BAR", "FOO"])
        def handle_contain(_event: dict[str, Any]) -> str:
            return "BAR"

        @app.contain("a", "b", "c")
        def handle_foo(_event: dict[str, Any]) -> str:
            return "contain"

        res = app.resolve({"a": ["b", "c"]})

        assert res == ["contain"]

    def test_resolve_multiple_routes(self) -> None:
        event = {"a": {"b": {"c": "TEST"}, "d": 1}}
        app = EventResolver(allow_multiple_routes=True)

        @app.when(Value("a.b.c").one_of(["TEST"]))
        async def handle_test(_event: dict[str, Any]) -> str:
            return "test"

        @app.equal("a.d", 1)
        def handle_d(_event: dict[str, Any]) -> str:
            return "d"

        res = app.resolve(event)

        assert res == ["test", "d"]

    def test_should_not_catch_exception_when_no_exception_handler(self) -> None:
        app = EventResolver()

        @app.one_of("a", ["BAR", "FOO"])
        def handle_contain(_event: dict[str, Any]) -> str:
            return "BAR"

        @app.contain("a", "b", "c")
        def handle_foo(_event: dict[str, Any]) -> str:
            raise ValueError("test")

        with pytest.raises(ValueError, match="test"):
            app.resolve({"a": ["b", "c"]})

    def test_should_not_catch_exception_when_no_exception_handler_for_this_error(self) -> None:
        app = EventResolver()

        @app.exception_handler(TypeError)
        def handle_value_error(exception: TypeError) -> str:
            return f"Something went wrong with value... {exception}"

        @app.contain("a", "b", "c")
        def handle_foo(_event: dict[str, Any]) -> str:
            raise ValueError("test")

        with pytest.raises(ValueError, match="test"):
            app.resolve({"a": ["b", "c"]})

    def test_should_exception_handler_when_error_raised(self) -> None:
        app = EventResolver()

        @app.exception_handler(ValueError)
        def handle_value_error(exception: ValueError) -> str:
            return f"Something went wrong with value... {exception}"

        @app.one_of("a", ["BAR", "FOO"])
        def handle_contain(_event: dict[str, Any]) -> str:
            return "BAR"

        @app.contain("a", "b", "c")
        def handle_foo(_event: dict[str, Any]) -> str:
            raise ValueError("test")

        assert app.resolve({"a": ["b", "c"]}) == ["Something went wrong with value... test"]

    def test_should_have_registered_all_exceptions_has_handled_when_passing_exception_list(
        self,
    ) -> None:
        app = EventResolver()

        @app.exception_handler([ValueError, TypeError])
        def handle_value_error(exception: ValueError | TypeError) -> str:
            return f"Something went wrong with error of {type(exception).__name__}..."

        @app.one_of("a", ["BAR", "FOO"])
        def handle_contain(_event: dict[str, Any]) -> str:
            raise TypeError

        @app.contain("a", "b", "c")
        def handle_foo(_event: dict[str, Any]) -> str:
            raise ValueError

        assert app.resolve({"a": ["b", "c"]}) == [
            "Something went wrong with error of ValueError..."
        ]
        assert app.resolve({"a": "BAR"}) == ["Something went wrong with error of TypeError..."]

    def test_should_handle_exception_even_if_base_exception_registered(self) -> None:
        class CustomValueError(ValueError): ...

        app = EventResolver()

        @app.exception_handler(ValueError)
        def handle_value_error(exception: ValueError) -> str:
            return f"Something went wrong with error of {type(exception).__name__}..."

        @app.contain("a", "b", "c")
        def handle_foo(_event: dict[str, Any]) -> str:
            raise CustomValueError

        assert app.resolve({"a": ["b", "c"]}) == [
            "Something went wrong with error of CustomValueError..."
        ]

    def test_include_routers(self) -> None:
        router_a = EventRouter()
        router_b = EventRouter()

        @router_a.equal("a", 1)
        def handle_a_1(event: dict[str, Any]) -> str:
            return "a-1"

        @router_a.equal("a", 2)
        def handle_a_2(event: dict[str, Any]) -> str:
            return "a-2"

        @router_b.equal("b", 1)
        def handle_b_1(event: dict[str, Any]) -> str:
            return "b-1"

        @router_b.equal("b", 2)
        def handle_b_2(event: dict[str, Any]) -> str:
            return "b-2"

        app = EventResolver()
        app.include_router(router_a, Value("name").equals("a"))
        app.include_router(router_b)

        assert app.resolve({"name": "a", "a": 2}) == ["a-2"]
        assert app.resolve({"name": "b", "b": 1}) == ["b-1"]

    def test_with_event_mapper(self) -> None:
        @dataclass
        class CartOperation:
            type: Literal["order_created", "order_update", "order_delete"]
            order_id: str
            user_id: float
            nb_items: int

        def to_cart_op(dto: dict[str, Any]) -> CartOperation:
            return CartOperation(
                order_id=dto["order_id"],
                type=dto["type"],
                user_id=dto["user_id"],
                nb_items=len(dto.get("cart", {}).get("items", [])),
            )

        app = EventResolver()

        # Order created and digital purchase.
        @app.when(Value("type").equals("order_created") & Value("cart.is_digital").is_truthy())
        @event_converter(to_cart_op)
        def handle_digital_purchase(event: CartOperation) -> str:
            return f"{event.order_id} has {event.nb_items} digital purchases"

        @app.one_of("type", ["order_update", "order_delete"])
        def handle_order_modification(event: dict[str, Any]) -> str:
            return f"Order modification <{event['type']}> : {event['order_id']}"

        assert app.resolve(
            {
                "type": "order_created",
                "order_id": "12345",
                "user_id": "67890",
                "cart": {"is_digital": True, "items": ["$10 voucher"]},
            }
        ) == ["12345 has 1 digital purchases"]

    def test_readme_simple(self) -> None:
        app = EventResolver()

        @app.equal("type", "order_created")
        def handler_order_created(event: dict[str, Any]) -> str:
            return f"Order created : {event['order_id']}"

        @app.one_of("type", ["order_update", "order_delete"])
        def handle_order_modification(event: dict[str, Any]) -> str:
            return f"Order modification <{event['type']}> : {event['order_id']}"

        assert app.resolve({"type": "order_created", "order_id": "12345", "user_id": "67890"}) == [
            "Order created : 12345"
        ]

        assert app.resolve({"type": "order_delete", "order_id": "12345", "user_id": "67890"}) == [
            "Order modification <order_delete> : 12345"
        ]

    def test_readme_complex(self) -> None:
        app = EventResolver()

        # Order created and digital purchase.
        @app.when(Value("type").equals("order_created") & Value("cart.is_digital").is_truthy())
        def handle_digital_purchase(event: dict[str, Any]) -> str:
            return f"The order created is a digital purchase: {event['order_id']}"

        # Order created and physical.
        @app.when(Value("type").equals("order_created") & Neg(Value("cart.is_digital").is_truthy()))
        def handle_physical_purchase(event: dict[str, Any]) -> str:
            return f"The order created is a physical purchase: {event['order_id']}"

        assert app.resolve(
            {
                "type": "order_created",
                "order_id": "12345",
                "user_id": "67890",
                "cart": {"is_digital": True, "items": ["$10 voucher"]},
            }
        ) == ["The order created is a digital purchase: 12345"]
        assert app.resolve(
            {
                "type": "order_created",
                "order_id": "12345",
                "user_id": "67890",
                "cart": {"is_digital": False, "items": ["keyboard"]},
            }
        ) == ["The order created is a physical purchase: 12345"]
