# Test exact box layout with Stage 4 fixed
stage_boxes = [
    {
        "num": 1,
        "w": 180,
        "lines": [
            "shell fork",
            "and execve"
        ]
    },
    {
        "num": 2,
        "w": 236,
        "lines": [
            "kernel checks",
            "the file and",
            "picks a",
            "format handler"
        ]
    },
    {
        "num": 3,
        "w": 190,
        "lines": [
            "ELF loader",
            "maps LOAD",
            "segments,",
            "builds the",
            "stack"
        ]
    },
    {
        "num": 4,
        "w": 236,
        "lines": [
            "PT_INTERP:",
            "kernel maps",
            "ld.so,",
            "execution",
            "starts in the",
            "dynamic linker"
        ]
    },
    {
        "num": 5,
        "w": 250,
        "lines": [
            "ld.so loads",
            "DT_NEEDED",
            "libraries,",
            "relocates, runs",
            "constructors"
        ]
    },
    {
        "num": 6,
        "w": 296,
        "lines": [
            "_start,",
            "__libc_start_main,",
            "main"
        ]
    }
]

total_w = sum(b["w"] for b in stage_boxes)
avail = 1520 # 1600 - 80 margins
gap = (avail - total_w) / 5
print(f"Total box width: {total_w} px")
print(f"Remaining for 5 gaps: {avail - total_w} px")
print(f"Each gap: {gap:.1f} px")

print("\nChecking paddings for every line in stage boxes:")
all_ok = True
for b in stage_boxes:
    print(f"\nStage {b['num']} (width={b['w']}):")
    for line in b["lines"]:
        w = len(line) * 24 * 0.60
        pad = (b["w"] - w) / 2
        ok = pad >= 16.0
        print(f"  '{line}' (len={len(line)}): w={w:.1f}px, pad={pad:.1f}px -> {'PASS' if ok else 'FAIL'}")
        if not ok:
            all_ok = False

assert all_ok, "Padding check failed!"
print("\nALL STAGE BOX PADDINGS PASS WITH >= 16px!")
