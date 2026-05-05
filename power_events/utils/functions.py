import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar, cast

from typing_extensions import ParamSpec

P = ParamSpec("P")
T = TypeVar("T")

# Type aliases
SyncFunc = Callable[P, T]
AsyncFunc = Callable[P, Awaitable[T]]
AnyFunc = SyncFunc[P, T] | AsyncFunc[P, T]


async def run_async(func: AnyFunc[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    """Run a sync or async function, always returning a coroutine."""
    if asyncio.iscoroutinefunction(func):
        return await cast(AsyncFunc[P, T], func)(*args, **kwargs)
    return await asyncio.to_thread(cast(SyncFunc[P, T], func), *args, **kwargs)
