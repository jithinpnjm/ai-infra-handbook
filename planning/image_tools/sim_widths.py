# Simulation script to test widths, wrapping, and heights for all boxes

def text_width(text, fs, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * factor * fs

def check_line(text, fs, is_mono=False):
    w = text_width(text, fs, is_mono)
    print(f"  [{fs}px {'mono' if is_mono else 'sans'}] len={len(text):2d}, w={w:6.1f}px : '{text}'")
    return w

print("--- 1. Top Lane: Task B blocking call ---")
check_line("time.sleep, requests.get,", 25, is_mono=True)
check_line("subprocess.run or heavy CPU", 25, is_mono=True)
check_line("time.sleep, requests.get, subprocess.run or heavy CPU", 24, is_mono=True)

print("\n--- 2. Top Lane: Stall warning ---")
check_line("a task is never paused except at an await,", 26, is_mono=False)
check_line("so all other tasks stall; timeouts fire everywhere", 26, is_mono=False)

print("\n--- 3. Routing Table: Row 1 ---")
check_line("blocking function", 28, is_mono=False)
check_line("await asyncio.to_thread(blocking_fn, args) (3.9)", 24, is_mono=True)
check_line("or loop.run_in_executor(executor, fn, *args)", 24, is_mono=True)

print("\n--- 4. Routing Table: Row 2 ---")
check_line("CPU-bound function", 28, is_mono=False)
check_line("run_in_executor with a ProcessPoolExecutor", 25, is_mono=True)

print("\n--- 5. Routing Table: Row 3 ---")
check_line("sync libraries requests, paramiko, boto3", 26, is_mono=True)
check_line("wrap with to_thread", 26, is_mono=True)

print("\n--- 6. Routing Table: Row 4 (Async libraries) ---")
# 168 chars:
# 'async libraries: aiohttp, httpx, asyncssh, aiofiles (uses threads under the hood), asyncpg, redis.asyncio, aiokafka, kubernetes_asyncio, aioboto3, aiobotocore, grpc.aio'
l1 = "async libraries: aiohttp, httpx, asyncssh, aiofiles (uses threads under the hood),"
l2 = "asyncpg, redis.asyncio, aiokafka, kubernetes_asyncio, aioboto3, aiobotocore, grpc.aio"
check_line(l1, 24, is_mono=True)
check_line(l2, 24, is_mono=True)

print("\n--- 7. Debug Strip ---")
# 301 chars:
# 'asyncio.run(main(), debug=True) or PYTHONASYNCIODEBUG=1 logs callbacks longer than 100 ms (loop.slow_callback_duration), coroutines never awaited and tasks destroyed while pending; asyncio.all_tasks() and task.print_stack() show where tasks are stuck; py-spy dump --pid when the loop itself is blocked'
d1 = "asyncio.run(main(), debug=True) or PYTHONASYNCIODEBUG=1 logs callbacks longer than 100 ms"
d2 = "(loop.slow_callback_duration), coroutines never awaited and tasks destroyed while pending;"
d3 = "asyncio.all_tasks() and task.print_stack() show where tasks are stuck;"
d4 = "py-spy dump --pid when the loop itself is blocked"
check_line(d1, 24, is_mono=True)
check_line(d2, 24, is_mono=True)
check_line(d3, 24, is_mono=True)
check_line(d4, 24, is_mono=True)

# Or 2 lines or 3 lines:
d_a = "asyncio.run(main(), debug=True) or PYTHONASYNCIODEBUG=1 logs callbacks longer than 100 ms (loop.slow_callback_duration),"
d_b = "coroutines never awaited and tasks destroyed while pending; asyncio.all_tasks() and task.print_stack() show where tasks are stuck;"
d_c = "py-spy dump --pid when the loop itself is blocked"
print("Debug strip 3-line split:")
check_line(d_a, 24, is_mono=True)
check_line(d_b, 24, is_mono=True)
check_line(d_c, 24, is_mono=True)

print("\n--- 8. Side Note: uvloop ---")
check_line("uvloop: faster drop-in loop on Linux and macOS", 25, is_mono=False)

print("\n--- 9. Bottom Bar ---")
check_line("Keep the loop free", 28, is_mono=False)
