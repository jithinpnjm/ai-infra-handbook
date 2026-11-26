import re

expected_labels = [
    "gather versus TaskGroup when one task fails",
    "gather(*aws, return_exceptions=False)",
    "first exception propagates, the other tasks keep running",
    "with 'return_exceptions=True' exceptions are collected in the results list alongside values",
    "async with asyncio.TaskGroup() as tg: tg.create_task(poll(n, results))",
    "tasks started in the group are awaited on exit",
    "if one fails the others are cancelled and an ExceptionGroup is raised",
    "except* TimeoutError as eg: log.error(timeouts: ..., [str(e) for e in eg.exceptions])",
    "return results",
    "asyncio.create_task(coro) schedules concurrently; keep a reference because the loop holds only weak references and a dropped task can be garbage collected mid-flight",
    "await suspends the caller until the awaited coroutine, future or task completes; only inside async def; calling an async def returns a coroutine object that has not run yet",
    "A TaskGroup leaves no orphan task behind"
]

print("Expected labels count:", len(expected_labels))
for i, l in enumerate(expected_labels):
    print(f"{i+1:2d}. {l}")
