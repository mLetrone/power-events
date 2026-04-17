# Event Converter

The `event_converter` decorator allows you to transform the raw event data into a more structured format before it is passed to your route handler.
This is particularly useful when you want to work with data classes or other custom objects instead of dictionaries.

## Basic Usage

Here's how you can use the `event_converter` to convert a dictionary into a Pydantic model:

```python
from pydantic import BaseModel
from power_events import EventResolver, event_converter

class User(BaseModel):
    name: str
    email: str

app = EventResolver()

@app.equal("type", "user_created")
@event_converter(User.model_validate)
def handle_user_created(user: User) -> None:
    print(f"User created: {user.name} ({user.email})")

event = {
    "type": "user_created",
    "name": "John Doe",
    "email": "john.doe@example.com"
}

app.resolve(event)
```

In this example, the `event_converter` takes any callable that maps the raw event dictionary to the desired type — here `User.model_validate`.
The `handle_user_created` function then receives a `User` object as its first argument instead of the raw event dictionary.
