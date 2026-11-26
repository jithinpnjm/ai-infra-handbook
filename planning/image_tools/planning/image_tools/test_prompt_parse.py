prompt_spec = """Title: How counter += 1 loses an update, and what the lock changes

CONTENT (use exactly these labels, each once, spelled exactly; add nothing else):
Two thread lanes and a shared variable counter. Without lock (top): the steps of counter += 1 are 'load, add, store'. Thread A loads counter = 5; thread B loads counter = 5; A adds and stores 6; B adds and stores 6; final counter is 6 where two increments should give 7 (orange: 'one update lost'). With lock (bottom): 'with lock:' makes load, add and store one protected unit; A holds the lock, B waits; A stores 6; B then loads 6 and stores 7. Code strip 'lock = threading.Lock(); def incr(n): global counter; for _ in range(n): with lock: counter += 1'. Related bugs strip 'data race: loses updates or breaks an invariant; deadlock: two threads each hold a lock the other needs; livelock: keep reacting without progress; starvation: a thread never gets its turn; priority inversion: a low-priority task holds a lock a high-priority task needs'. Habits strip 'keep critical sections tiny and free of I/O; never call unknown callbacks while holding a lock; prefer queues and immutable messages; test with stress loops'. Bottom bar: 'Without the lock, the steps interleave'."""

import re

# Look at quotes:
quoted = re.findall(r"'([^']*)'", prompt_spec)
print(f"Quoted count: {len(quoted)}")
for q in quoted:
    print(" -", q)
