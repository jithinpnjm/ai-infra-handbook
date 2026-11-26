import re

# Conservative text width calculation
# sans 0.6 * font-size * chars, monospace 0.62 * font-size * chars

boxes_and_text = [
    # (box_desc, box_width, text, font_type, font_size)
    ("Formula Box", 620, "Total cycles = K * (N - 1) + S", "mono", 26),
    ("Top Lane Title in Lane Container", 1500, "Without a pipeline", "sans", 32),
    ("Stage 1 Box line 1", 265, "load from", "sans", 24),
    ("Stage 1 Box line 2", 265, "memory", "sans", 24),
    ("Stage 2 Box line 1", 265, "normalize", "sans", 24),
    ("Stage 2 Box line 2", 265, "mantissas", "sans", 24),
    ("Stage 3 Box", 265, "add", "sans", 26),
    ("Stage 4 Box", 265, "correct", "sans", 26),
    ("Stage 5 Box line 1", 265, "write result", "sans", 24),
    ("Stage 5 Box line 2", 265, "back", "sans", 24),
    ("Label under Top Lane", 720, "500 cycles for N = 100 elements with S = 5", "sans", 25),
    ("Bottom Lane Title in Lane Container", 1500, "With a pipeline", "sans", 32),
    ("Orange Highlight Pill/Band", 1449, "pipeline fill time (S cycles)", "sans", 24),
    ("Label under Bottom Lane", 880, "104 cycles = K x (N - 1) + S, with K = 1, N = 100, S = 5", "sans", 25),
    ("Plain Note at Bottom", 760, "pipelining is a different idea from vectorization", "sans", 24),
]

print("Checking text line paddings (conservative rule >= 16px):")
for desc, bw, text, ftype, fsize in boxes_and_text:
    factor = 0.62 if ftype == "mono" else 0.6
    tw = len(text) * factor * fsize
    pad = (bw - tw) / 2.0
    print(f"[{'PASS' if pad >= 16 else 'FAIL'}] {desc}: box={bw}px, tw={tw:.1f}px, pad={pad:.1f}px (len={len(text)})")
    assert pad >= 16, f"Padding {pad} < 16 for {desc}"

print("\nALL TEXT PADDINGS >= 16px PASS!")
