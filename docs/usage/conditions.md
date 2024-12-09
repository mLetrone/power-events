The true power of **Power-event** lies on its condition system.
It can combine multiple conditions the same way it's possible in [Boolean Algebra](https://en.wikipedia.org/wiki/Boolean_algebra).

This way, you can use these operators:
=== "AND"
    ```python
    from power_events.conditions import And

    condition1 & condition2
    # Or this way
    And(condition1, condition2, ...)
    ```
=== "OR"
    ```python
    from power_events.conditions import Or

    condition1 | condition2
    # Or this way
    Or(condition1, condition2, ...)
    ```
=== "NOT"
    ```python
    from power_events.conditions import Neg

    ~condition1
    # Or this way
    Neg(condition1)
    ```

## What's a condition?

A condition is defined by **two** things:

- A set of predicates to a certain value (precisely a _path to value in the event_), to verify if the event matches it.

- And as said previously, the ability to be compatible with *Boolean Algebra*.

## Let's create some

The entrypoint to create a condition is [`Value`](../api/value.md/#conditions.value.Value).
With which, we define the value path in the event to check under the predicate given.

### Path

The path to a value is a string containing all the keys to reach it inside an event.
It allows getting a value at any depth level, whether the value is there or not.

Each key should be separated by a `.`,
otherwise it may:

- Either raise a validation error.
    - By beginning by separator. `.menu` :x:
    - By ending by separator. `menu.` :x:
    - Use consecutive separators. `menu..dessert` :x:
- Or worst, not work as expected!


```python
from power_events.conditions import ValuePath

event = {}

# this path
value = ValuePath("menu.desserts.parfait").get_from(event, default=None)

# is equivalent to this with the event
value = event.get("menu", {}).get("desserts", {}).get("parfait")
```

I don't know about you, but I prefer to read the first way with the `ValuePath`, don't you?

_yep totally biased :shushing_face:_

### Predicate

To add predicate at the value check, you can either use built-in method (like [`equals`](../api/value.md/#conditions.value.Value.equals), [`one_of`](../api/value.md/#conditions.value.Value.one_of), etc.),
or using yours, passing it to the method [`match`](../api/value.md/#conditions.value.Value.match).

!!! info
    Each time you add a predicate to a `Value` object, it's combined with its current.

```python
from power_events.conditions import Value

desserts_minimum_selection = Value("menu.desserts").contains("parfait", "crepes", "cookie")
parfait_price_cond = Value("menu.desserts.parfait.price").match(lambda price: 0 < price < 10)

event = {
    "restaurant": "La maison",
    "menu": {
        "entrees": {},
        "dishes": {},
        "desserts": {
            "flan": {},
            "crepes": {},
            "parfait": {
                "price": 6.5
            },
            "cookie": {}
        }
    }
}
""" Here we check that the menu as minimum cookie, crepes and parfait as dessert,
*and* parfait price is between $0 and $10.
"""
assert (desserts_minimum_selection & parfait_price_cond).check(event)
```
!!! info "Things to know"

    * String and integer keys are supported.
    * If the value is **absent**:
        * By default, the event **fails** the condition.
        * You can raise an error using the option `raise_if_absent`, and a [`ValueAbsentError`](../api/exception.md/#exceptions.ValueAbsentError) exception will be raised.

### Mapping

Sometimes, the value in the event has been serialized to simplify the format, like date passed as timestamp or iso format.
You can provide a mapper, to choose how the value will be checked.

An example with a date, the menu carte should be the menu of the week. But the date is represented as a string.

```python
from datetime import datetime, timedelta

from power_events.conditions import Value

DATE_FORMAT = "%Y-%m-%d"


def to_datetime(value: str) -> datetime:
    return datetime.strptime(value, DATE_FORMAT)


date_cond = Value("effective-date", to_datetime).match(lambda val: val >= (datetime.now() - timedelta(weeks=1)))

event = {
    "restaurant": "La maison",
    "effective-date": (datetime.now() - timedelta(days=2)).strftime(DATE_FORMAT),
    "menu": {
        "entrees": {},
        "dishes": {},
        "desserts": {}
    }
}

assert date_cond.check(event)
```

### Combination

As show before, it's possible to combine `Value` (using And or Or logic).
But it's also possible to combine the resulting condition, and so on, to have a tree of conditions.

To have something like this:

=== "Code"
    ```python
    from typing import Union

    from power_events.conditions import Value

    desserts_minimum_selection = Value("menu.desserts").contains("parfait", "crepes", "cookie")

    def valid_range_price(price: Union[float, int]) -> bool:
        return 0 < price < 10

    parfait_price_cond = Value("menu.desserts.parfait.price").match(valid_range_price)
    crepes_price_cond = Value("menu.desserts.crepes.price").match(valid_range_price)

    restaurant_name_cond = Value("restaurant").is_not_empty()

    condition = restaurant_name_cond & (
        desserts_minimum_selection & (parfait_price_cond | crepes_price_cond)
        )
    ```
=== "Graph"
    ``` mermaid
    graph TD
        A[AND] --> B[restaurant_name_cond]
        A --> C[AND]
        C --> D[desserts_minimum_selection]
        C --> E[OR]
        E --> F[parfait_price_cond]
        E --> H[crepes_price_cond]
    ```
