import re

def wrap_text(text, max_w, fs=24, is_mono=False):
    char_w = fs * (0.62 if is_mono else 0.60)
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test = " ".join(cur + [w])
        if len(test) * char_w <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines

# In 3 columns:
lane_w = 480
inner_w = lane_w - 48 # 432 px

lane1_body = "one interpreter runs jobs 0 to 7 one after another"
print("Lane 1 Body wrapped in 432px:")
for l in wrap_text(lane1_body, inner_w, fs=24):
    w = len(l) * 24 * 0.6
    print(f"  '{l}' (w={w:.1f}, rem={inner_w - w:.1f})")

lane2_body = "four threads share one GIL and take turns, so 'about as long as sequential, or a little longer'"
print("\nLane 2 Body wrapped in 432px:")
for l in wrap_text(lane2_body, inner_w, fs=24):
    w = len(l) * 24 * 0.6
    print(f"  '{l}' (w={w:.1f}, rem={inner_w - w:.1f})")

lane3_body = "four interpreters, each with its own GIL, 'clearly faster' on a machine with at least four free cores"
print("\nLane 3 Body wrapped in 432px:")
for l in wrap_text(lane3_body, inner_w, fs=24):
    w = len(l) * 24 * 0.6
    print(f"  '{l}' (w={w:.1f}, rem={inner_w - w:.1f})")

side_note = "change burn to time.sleep(1) and rerun: now threads win because the GIL is released while a thread sleeps"
print("\nSide note wrapped in 1440px:")
for l in wrap_text(side_note, 1440, fs=24):
    w = len(l) * 24 * 0.6
    print(f"  '{l}' (w={w:.1f}, rem={1440 - w:.1f})")

strip = "timed() prints label and seconds with perf_counter; your timings depend on your hardware, so record your own"
print("\nStrip wrapped in 1440px:")
for l in wrap_text(strip, 1440, fs=24):
    w = len(l) * 24 * 0.6
    print(f"  '{l}' (w={w:.1f}, rem={1440 - w:.1f})")

footnote = "a thread that computes for a long time is paused every 5 ms (sys.getswitchinterval()), an asyncio task is never paused that way and runs until an await"
print("\nFootnote wrapped in 1440px:")
for l in wrap_text(footnote, 1440, fs=24):
    w = len(l) * 24 * 0.6
    print(f"  '{l}' (w={w:.1f}, rem={1440 - w:.1f})")
