import xml.etree.ElementTree as ET
import re

# Test script to design and verify layout for p3-0306-blocking-loop-fix
title = "One blocking call freezes every task, and how to route work off the loop"
spec = """Top lane: a single event loop thread with tasks A, B, C. Task B calls 'time.sleep, requests.get, subprocess.run or heavy CPU' (orange): 'a task is never paused except at an await, so all other tasks stall; timeouts fire everywhere'. Bottom routing table: 'blocking function' to 'await asyncio.to_thread(blocking_fn, args) (3.9) or loop.run_in_executor(executor, fn, *args)'; 'CPU-bound function' to 'run_in_executor with a ProcessPoolExecutor'; 'sync libraries requests, paramiko, boto3' to 'wrap with to_thread'; 'async libraries: aiohttp, httpx, asyncssh, aiofiles (uses threads under the hood), asyncpg, redis.asyncio, aiokafka, kubernetes_asyncio, aioboto3, aiobotocore, grpc.aio'. Debug strip 'asyncio.run(main(), debug=True) or PYTHONASYNCIODEBUG=1 logs callbacks longer than 100 ms (loop.slow_callback_duration), coroutines never awaited and tasks destroyed while pending; asyncio.all_tasks() and task.print_stack() show where tasks are stuck; py-spy dump --pid when the loop itself is blocked'. Side note 'uvloop: faster drop-in loop on Linux and macOS'. Bottom bar: 'Keep the loop free'."""

quotes = re.findall(r"'([^']+)'", spec)
expected_labels = [title] + quotes

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels):
    print(f"{i:2d}. len={len(l):3d}: {l}")
