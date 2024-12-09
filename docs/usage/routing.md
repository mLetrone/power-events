# Event handling

Now we have the basis, let's deep dive a bit further to have a global view of the features.

## Options

When declaring an event resolver, some options can be passed depending on you need.
!!! tip
    If you feel like some options or functionalities are missing, feel free to open
    an [issue](https://github.com/mLetrone/power-events/issues){target="_blank"} :smile:!
    
    More could arrive this way.

### Multiple routes

To prevent unexpected behaviour, by default an event meeting conditions of different routes, will raise `MultipleRouteError`.
However, in case of intended multiple routes conditions matching an event.
The option `allow_multiple_route` at resolver definition can be passed; this way, all routes passing will be called.

=== "Default"
    ```python
    from power_events import EventResolver
    
    app = EventResolver()
    
    @app.one_of("type", ["create", "delete"])
    def handle_operation(event: dict) -> None:
        """Some logic."""
        
    @app.equal("type", "delete")
    def handle_deletion(event: dict) -> None:
        """Deletion logic"""
        
    event = {
        "type": "delete"
        # Other fields
    }
    
    app.resolve(event)
    E   power_events.exceptions.MultipleRoutesError: Multiples routes found for the current event: {'type': 'delete'}.
    E   Available route functions are handle_operation, handle_deletion.
    E   If it's normal pass the option 'allow_multiple_routes' in the resolver definition.
    ```
=== "With `allow_multiple_route` option"
    ```python
    from power_events import EventResolver
    
    app = EventResolver(allow_multiple_routes=True)
    
    @app.one_of("type", ["create", "delete"])
    def handle_operation(event: dict) -> None:
        """Some logic."""
        
    @app.equal("type", "delete")
    def handle_deletion(event: dict) -> None:
        """Deletion logic"""
        
    event = {
        "type": "delete"
        # Other fields
    }
    
    app.resolve(event) # no error
    # handle_operation and handle_deletion call

    ```

### No route

Because all events may not have to be processed by your application, by default **power-events** allow it.

Of course, you can raise an error otherwise when an event doesn't meet any route. Same as before, just an option.
Pass `allow_no_route` to `False`, and it's done!

=== "Default"
    ```python
    from power_events import EventResolver
    
    app = EventResolver()
    
    @app.one_of("type", ["create", "delete"])
    def handle_operation(event: dict) -> None:
        """Some logic."""
        
    @app.equal("type", "delete")
    def handle_deletion(event: dict) -> None:
        """Deletion logic"""
        
    event = {
        "type": "update"
        # Other fields
    }
    
    app.resolve(event) # no route has been called.
    ```
=== "Without `allow_no_route` option"
    ```python
    from power_events import EventResolver
    
    app = EventResolver(allow_no_route=False)
    
    @app.one_of("type", ["create", "delete"])
    def handle_operation(event: dict) -> None:
        """Some logic."""
        
    @app.equal("type", "delete")
    def handle_deletion(event: dict) -> None:
        """Deletion logic"""
        
    event = {
        "type": "delete"
        # Other fields
    }
    
    app.resolve(event)
    >>> power_events.exceptions.NoRouteFoundError: No route found for the current event: {'a': 1}.
    >>> Registered route functions are .
    >>> If it's normal pass the option 'allow_no_route' at `False` in the resolver definition.


    ```


## Route

### Built-in conditions

As saw before, it is possible to register a route using built-in condition preset.

- [equal](../api/resolver.md#resolver.EventResolver.equal): when one field should be equal.
- [one_of](../api/resolver.md#resolver.EventResolver.one_of): when one field should be one of the options.
- [contain](../api/resolver.md#resolver.EventResolver.contain): when one field should contain item(s).

```python title="Built-in condition route"
from typing import Any

from power_events import EventResolver

app = EventResolver()

@app.equal("my-field1", 1)
def handle_route_1(event: dict) -> Any:
    """route logic."""
```

### Custom conditions

But often, business logic is not that simple.
It needs to rely on more than one field, and much, much, much more complex and subtle condition.

**No Problem!**

The core has been designed to meet any condition without concession.
!!! info
    For that, if you haven't checked the section about [condition](conditions.md), check it out before continuing :wink:.

We can use custom conditions,
 using either built-in predicate function or your own,
 and combine it with different event fields.
As another possibility, you can also perform a condition over the whole event itself by the [`Value.root`](../api/value.md#conditions.value.Value.root).

[`when`](../api/resolver.md#resolver.EventResolver.when) is here to respond to any use case above. All condition concepts are usable!

```python
from datetime import datetime, date
from power_events.conditions import Value
from power_events import EventResolver

app = EventResolver()


def my_predicate(value: str) -> bool:
    """condition logic."""


def to_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


@app.when(Value("body").match(my_predicate))
def handle_field(event: dict) -> None:
    """Route on 'body' value"""


@app.when(Value.root().contains("error"))
def handle_field(event: dict) -> None:
    """Route if event contains 'error'"""


@app.when(Value("body.date", to_date).equals(lambda val: val == date.today()) 
          & Value("body.name").equals("creation"))
def handle_today_creation(event: dict) -> None:
    """Route if event body date is today and it's a creation"""
```

### Fallback

As mentioned above, we can have no routes that match our event, and choose whether to raise an error or not.
Another way is to use the `fallback` decorator to override the other behaviours.

The function will only be called when **no route has been found** to handle the current event.

```python title="Define fallback route"
from typing import Any

from power_events import EventResolver

app = EventResolver()

@app.equal("body.name", "creation")
def handle_creation(event: dict[str, Any]) -> str:
    return "creation"

@app.fallback()
def fallback(event: dict[str, Any]) -> str:
    return "fallback"
```

## Exception handling

You can add a custom exception handler with any Python exception.
This allows handling this kind of exception globally and not inside each of your routes.

Let's say you have to deal with `ValidationError` that your code (or used library) might raise.
You want to add a specific behaviour when this occurs (default value, log, REST API call, metrics, send message, etc.).


```python title="Exception handling"
from logging import Logger

from power_events import EventResolver
from power_events.conditions import ValuePath

logger = Logger("power-events")


class ValidationError(Exception):
    pass


app = EventResolver()


@app.exception_handler(ValidationError)
def validation_exception_handler(exc: ValidationError) -> None:
    """Your handling logic"""
    logger.error(f"Malformed event: {exc}")


@app.equal("body.name", "creation")
def handle_creation(event: dict):
    sender = ValuePath("body.sender").get_from(event)
    if sender == "unknown":
        raise ValidationError("unknown sender")

    return {"sender": sender, "status": "created"}
```

Here, if we get an event where the sender is `"unknown"`, the route will raise a `ValidationError`.
But `validation_exception_handler` will handle it.

!!! info
    The `exception_handler` can also:
    
    - support passing a list of exception types to be handled with one handler.
    - handle exception like `except` (resolve inheritance).
