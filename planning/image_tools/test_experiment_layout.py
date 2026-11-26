import re

title = "The ten-minute experiment: the same job run three ways"
subtitle = "Three lanes for 8 jobs of burn(seed), each chaining 1,000,000 SHA-256 hashes."
lane1_title = "sequential"
lane1_body = "one interpreter runs jobs 0 to 7 one after another"
lane2_title = "4 threads: ThreadPoolExecutor(max_workers=4)"
lane2_body = "four threads share one GIL and take turns, so 'about as long as sequential, or a little longer'"
lane3_title = "4 processes: ProcessPoolExecutor(max_workers=4)"
lane3_body = "four interpreters, each with its own GIL, 'clearly faster' on a machine with at least four free cores"
side_note = "change burn to time.sleep(1) and rerun: now threads win because the GIL is released while a thread sleeps"
strip = "timed() prints label and seconds with perf_counter; your timings depend on your hardware, so record your own"
footnote = "a thread that computes for a long time is paused every 5 ms (sys.getswitchinterval()), an asyncio task is never paused that way and runs until an await"
bottom_bar = "The GIL gives threads turns, processes get their own lock"

labels = [
    title,
    subtitle,
    lane1_title,
    lane1_body,
    lane2_title,
    lane2_body,
    lane3_title,
    lane3_body,
    side_note,
    strip,
    footnote,
    bottom_bar
]

print("Total labels:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. len={len(l):3d}: '{l}'")
