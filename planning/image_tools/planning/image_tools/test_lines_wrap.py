#!/usr/bin/env python3
import re

def calc_width(segments):
    total = 0.0
    for text, fs, is_mono in segments:
        rate = 0.62 if is_mono else 0.60
        total += len(text) * rate * fs
    return total

def test_box_lines(box_id, lines, max_w=416):
    all_ok = True
    print(f"\n==================== BOX {box_id} (max_w={max_w}) ====================")
    for idx, line in enumerate(lines):
        w = calc_width(line)
        line_str = "".join(t for t, fs, m in line)
        ok = (w <= max_w)
        if not ok:
            all_ok = False
        print(f"  Line {idx+1:2d} (w={w:5.1f}px, ok={str(ok):5s}): '{line_str}'")
    joined = " ".join("".join(t for t, fs, m in line) for line in lines)
    cleaned = re.sub(r'\s+', ' ', joined).strip()
    return cleaned, all_ok

# Box 5:
b5_lines = [
    [("Warm-up:", 30, False)],
    [("allocate KV pool, profile,", 24, False)],
    [("compile and capture", 24, False)],
    [("CUDA graphs:", 24, False)],
    # Remedy
    [("reuse the ", 24, False), ("torch.compile", 24, True)],
    [("cache under ", 24, False), ("VLLM_CACHE_ROOT,", 24, True)],
    [("set ", 24, False), ("VLLM_FORCE_AOT_LOAD=1", 24, True)],
    [("to fail loudly on a", 24, False)],
    [("cache miss, pass", 24, False)],
    [("--kv-cache-memory", 24, True)],
    [("to skip profiling", 24, False)]
]
t5, ok5 = test_box_lines(5, b5_lines)
exp5 = "Warm-up: allocate KV pool, profile, compile and capture CUDA graphs: reuse the torch.compile cache under VLLM_CACHE_ROOT, set VLLM_FORCE_AOT_LOAD=1 to fail loudly on a cache miss, pass --kv-cache-memory to skip profiling"
assert t5 == exp5, f"Mismatch 5:\n{t5}\nvs\n{exp5}"
assert ok5

# Footer:
footer_lines = [
    [("book says these together can cut scale-up from many minutes to tens of seconds", 24, False)],
    [("depending on model size; ", 24, False), ("--enforce-eager", 24, True), (" and ", 24, False), ("-O0", 24, True), (" make boot fast but decode slower,", 24, False)],
    [("use them in development only; most time goes to model download and weight load;", 24, False)],
    [("measure each phase on your own cluster", 24, False)]
]
t_foot, ok_foot = test_box_lines("Footer", footer_lines, max_w=1472)
exp_foot = "book says these together can cut scale-up from many minutes to tens of seconds depending on model size; --enforce-eager and -O0 make boot fast but decode slower, use them in development only; most time goes to model download and weight load; measure each phase on your own cluster"
assert t_foot == exp_foot
assert ok_foot

print("\n>>> BOX 5 AND FOOTER PASSED PERFECTLY! <<<")
