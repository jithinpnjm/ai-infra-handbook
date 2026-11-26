import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_test.svg")
root = tree.getroot()

# Map each text to its containing rect
text_rect_pairs = [
    # (text, font_family, fs, is_mono, rect_coords: x, y, w, h, align)
    ("gather versus TaskGroup when one task fails", "sans-serif", 48, False, (0, 0, 1600, 95), "middle"),
    ("gather(*aws, return_exceptions=False)", "monospace", 30, True, (40, 95, 1520, 280), "left"),
    ("first exception propagates, \nthe other tasks keep running", "sans-serif", 24, False, (690, 175, 845, 85), "middle"),
    ("with 'return_exceptions=True' exceptions are \ncollected in the results list alongside values", "sans-serif", 24, False, (690, 270, 845, 85), "middle"),
    ("async with asyncio.TaskGroup() as tg: tg.create_task(poll(n, results))", "monospace", 30, True, (40, 395, 1520, 360), "left"),
    ("tasks started in the group are awaited on exit", "sans-serif", 24, False, (690, 475, 845, 70), "middle"),
    ("if one fails the others are cancelled \nand an ExceptionGroup is raised", "sans-serif", 24, False, (690, 555, 845, 75), "middle"),
    ("except* TimeoutError as eg:\n  log.error(timeouts: ..., \n  [str(e) for e in eg.exceptions])", "monospace", 24, True, (690, 640, 560, 95), "left"),
    ("return results", "monospace", 24, True, (1270, 640, 265, 95), "middle"),
    ("asyncio.create_task(coro) schedules concurrently; keep a reference because the loop holds \nonly weak references and a dropped task can be garbage collected mid-flight", "sans-serif", 24, False, (40, 775, 1520, 85), "left"),
    ("await suspends the caller until the awaited coroutine, future or task completes; only inside \nasync def; calling an async def returns a coroutine object that has not run yet", "sans-serif", 24, False, (40, 880, 1520, 85), "left"),
    ("A TaskGroup leaves no orphan task behind", "sans-serif", 28, False, (40, 985, 1520, 65), "middle"),
]

for label, ff, fs, is_mono, (bx, by, bw, bh), align in text_rect_pairs:
    lines = label.split('\n')
    coeff = 0.62 if is_mono else 0.6
    for l in lines:
        tw = len(l) * coeff * fs
        if align == "middle":
            pad = (bw - tw) / 2
        else: # left
            # assuming text starts with padding
            pad = bw - tw
        print(f"[{pad:5.1f}px pad] '{l[:40]}' (tw={tw:.1f}, bw={bw})")
        assert pad >= 16, f"Padding {pad} < 16 for '{l}' in box width {bw}"

print("\nALL TEXT PADDINGS >= 16px! (PASS)")
