c3_5lines = [
    "server fails mid-stream: a data: error chunk",
    "and [DONE] under HTTP 200; the engine",
    "counts it as finished_reason error;",
    "a client disconnect is counted",
    "as abort"
]

print("--- 5 lines in width 740 ---")
for l in c3_5lines:
    w = len(l) * 0.6 * 24
    pad = (740 - w) / 2
    print(f"  '{l}': len={len(l)}, w={w:.1f}, pad={pad:.1f}, ok={pad>=16}")
