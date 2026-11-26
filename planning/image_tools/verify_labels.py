import re

spec = """A table 'Question' to 'Tool'. 'Where is every thread stuck right now?' / 'faulthandler.enable(), faulthandler.dump_traceback_later(timeout, repeat=True), kill -SIGUSR1 with faulthandler.register'. 'Look at a running process without changing its code' / 'py-spy dump, py-spy top, py-spy record'. 'What threads and tasks exist?' / 'threading.enumerate(), sys._current_frames(), asyncio.all_tasks(), psutil.Process().num_threads()'. 'Sockets and descriptors' / 'ss -s, lsof -p'. 'System calls and CPU' / 'strace -f -p, perf'. 'Where memory grows' / 'tracemalloc'. 'Health metrics to track' / 'in-flight tasks, queue depth, latency percentiles' (orange). Chain strip 'symptom, then faulthandler dump or py-spy dump, then the cause in the pitfall table'. Bottom bar: 'Sample the live process before you guess'."""

# Labels in single quotes
matches = re.findall(r"'([^']+)'", spec)
print("Quoted labels found in spec:")
for idx, m in enumerate(matches):
    print(f"{idx+1}: {m}")
