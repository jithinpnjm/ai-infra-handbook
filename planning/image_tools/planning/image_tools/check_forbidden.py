import re

expected_labels = [
    "How counter += 1 loses an update, and what the lock changes",
    "Two thread lanes and a shared variable counter",
    "Without lock",
    "the steps of counter += 1 are 'load, add, store'",
    "Thread A",
    "counter",
    "Thread B",
    "Thread A loads counter = 5",
    "thread B loads counter = 5",
    "A adds and stores 6",
    "B adds and stores 6",
    "final counter is 6 where two increments should give 7",
    "one update lost",
    "With lock",
    "'with lock:' makes load, add and store one protected unit",
    "A holds the lock, B waits",
    "A stores 6",
    "B then loads 6 and stores 7",
    "lock = threading.Lock(); def incr(n): global counter; for _ in range(n): with lock: counter += 1",
    "data race: loses updates or breaks an invariant",
    "deadlock: two threads each hold a lock the other needs",
    "livelock: keep reacting without progress",
    "starvation: a thread never gets its turn",
    "priority inversion: a low-priority task holds a lock a high-priority task needs",
    "keep critical sections tiny and free of I/O",
    "never call unknown callbacks while holding a lock",
    "prefer queues and immutable messages",
    "test with stress loops",
    "Without the lock, the steps interleave"
]

forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for l in expected_labels:
    for f in forbidden:
        if re.search(r'\b' + f + r'\b', l.lower()):
            print(f"WARNING: forbidden word '{f}' in '{l}'")

print("Forbidden words check in expected_labels: DONE")
