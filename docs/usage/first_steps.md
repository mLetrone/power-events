# First steps

The simplest example could look like this:

```python
from power_events import EventResolver

app = EventResolver()

@app.equal("type", "power-event")
def handle_example(event):
    return "Hello from power-event type event"


print(app.resolve({"type": "power-event"}))
# ["Hello from power-event type event"]
```

## Recap, step by step

### Step 1: create an `EventResolver`

```python hl_lines="3"
from power_events import EventResolver

app = EventResolver()

@app.equal("type", "power-event")
def handle_example(event):
    return "Hello from power-event type event"


print(app.resolve({"type": "power-event"}))
# ["Hello from power-event type event"]
```

Here `app` will be an instance of [`EventResolver`](../api/resolver.md/#resolver.EventResolver), it's the main entrypoint to define our event routes.

### Step 2: create an event route operation

#### Path

"Path" here refers to our [condition path](conditions.md/#path), it's the path of our value inside the event.

#### Condition operation

"Operation" can be either built-in operation like one of:

- `equal`
- `one_of`
- `contain`

Or custom passing ours with `when`.

### Define our route

```python hl_lines="5 6"
from power_events import EventResolver

app = EventResolver()

@app.equal("type", "power-event")
def handle_example(event):
    return "Hello from power-event type event"


print(app.resolve({"type": "power-event"}))
# ["Hello from power-event type event"]
```

`@app.equal("type", "power-event")` tells at **Power-Events** that the function defines below to be triggered if an event with the value at path `type` is equals at `power-event`.

!!! info "About `@decorator`"

    the `@` syntax in Python is called a "decorator".

    It's a shorthand to `decorator(function)`.

    A decorator is a function that takes a function to do something with it.

    In our case, it registers the function in our Resolver, that way it will be called corresponding to the condition given. Here when 'type' is equal to 'power-event'.

### Function constraint

```python hl_lines="6"
from power_events import EventResolver

app = EventResolver()

@app.equal("type", "power-event")
def handle_example(event):
    return "Hello from power-event type event"


print(app.resolve({"type": "power-event"}))
# ["Hello from power-event type event"]
```

Currently, there is a one constraint on the function handler signature, it should have as first argument the event.

Otherwise, a TypeError will occur saying an argument was passed.
