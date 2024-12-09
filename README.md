# Power-Events
<div align="center" style="margin:40px;">
<!-- --8<-- [start:overview-header] -->

  [![Test](https://github.com/MLetrone/power-events/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/MLetrone/power-events/actions/workflows/ci.yml)
  [![Coverage](https://coverage-badge.samuelcolvin.workers.dev/MLetrone/power-events.svg)](https://coverage-badge.samuelcolvin.workers.dev/redirect/MLetrone/power-events)
  [![Language](https://img.shields.io/badge/Language-python≥3.9-3776ab?style=flat-square&logo=Python)](https://www.python.org/)
  ![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)
  ![Style](https://img.shields.io/badge/Style-ruff-9a9a9a?style=flat-square)
  ![Lint](https://img.shields.io/badge/Lint-ruff,%20mypy-brightgreen?style=flat-square)

<!-- --8<-- [end:overview-header] -->

---

Source Code: [https://github.com/MLetrone/power-events](https://github.com/MLetrone/power-events)

documentation: [https://mletrone.github.io/power-events](https://mletrone.github.io/power-events/)

---
</div>
<!-- --8<-- [start:overview-body] -->

_Take control of your event routing, effortlessly and tailored to your needs._

## Description

**Power-events** is a lightweight yet powerful library that manages event routing by defining routes with precise conditions,
inspired by FastAPI’s endpoint routing system.
It simplifies the organization of complex events by applying specific routing rules defined
 by the user and enables actions to be triggered in response to events in a structured manner.

## Key features:
- **Syntax**: Lean to standards like Powertools or FastAPI.
- **Easy**: Design to be easy to read and use.
- **Flexible**: You can do whatever condition at any depth level in your event.
- **Fully tested**: 100% coverage.
- **Fully typed**: compatible out of the box with `mypy` !
- **Lightweight**

<!-- --8<-- [end:overview-body] -->
## installation

```shell
pip install power-events
```

That's all! _Ready to use_
<!-- --8<-- [start:body] -->
## Examples
---
### Simple conditions

- create a `main.py` with:

```python
from typing import Any
from power_events import EventResolver

app = EventResolver()

@app.equal("type", "order_created")
def handler_order_created(event: dict[str, Any]) -> str:
  return f"Order created: {event['order_id']}"

@app.one_of("type", ["order_update", "order_delete"])
def handle_order_modification(event: dict[str, Any]) -> str:
  return f"Order modification <{event['type']}>: {event['order_id']}"

```

- use routing:

> N.B: assert is here to show which route has been called.
> In real condition, don't need to use it.

```python
assert app.resolve({
    "type": "order_created",
    "order_id": "12345",
    "user_id": "67890"
}) == ["Order created: 12345"]
# Note: `resolve` returns a list, because you can allow multiple routes for one event.

assert app.resolve({
    "type": "order_delete",
    "order_id": "12345",
    "user_id": "67890"
})== ["Order modification <order_delete>: 12345"]

```
### Complex conditions

_In depth field condition and condition combinations_

```python
from power_events import EventResolver
from power_events.conditions import Value, Neg

app = EventResolver()

# Order created and digital purchase.
@app.when(Value("type").equals("order_created") & Value("cart.is_digital").is_truthy())
def handle_digital_purchase(event: dict) -> str:
    return f"The order created is a digital purchase: {event['order_id']}"

# Order created and physical.
@app.when(Value("type").equals("order_created") & Neg(Value("cart.is_digital").is_truthy()))
def handle_physical_purchase(event: dict) -> str:
    return f"The order created is a physical purchase: {event['order_id']}"


assert app.resolve({
    "type": "order_created",
    "order_id": "12345",
    "user_id": "67890",
    "cart": {
        "is_digital": True,
        "items": [
            "$10 voucher"
        ]
    }
}) == ["The order created is a digital purchase: 12345"]
assert app.resolve({
    "type": "order_created",
    "order_id": "12345",
    "user_id": "67890",
    "cart": {
        "is_digital": False,
        "items": [
            "keyboard"
        ]
    }
}) == ["The order created is a physical purchase: 12345"]
```

It's possible to perform `OR`, `AND`, `NEG` operation over conditions.
<!-- --8<-- [end:body] -->
