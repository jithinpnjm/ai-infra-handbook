import xml.etree.ElementTree as ET

tree = ET.parse("test_ipc_candidate.svg")
root = tree.getroot()

# Let's inspect each text element and its bounding boxes
print("Auditing line lengths and paddings...")

# Let's check text lines inside boxes:
# 1. Left zone advice box: rect x=85, y=420, w=420, h=165
# lines:
advice1_lines = [
    "Faster memory,",
    "better locality,",
    "fewer memory accesses;",
    "check NUMA, cache misses,",
    "TLB; consider huge pages,",
    "binding, data layout"
]
for line in advice1_lines:
    w = len(line) * 24 * 0.6
    print(f"Advice1 line: '{line}' ({len(line)} chars) -> width {w:.1f}px in 420px box (padding = {(420-w)/2:.1f}px)")
    assert (420 - w)/2 >= 16

# 2. Middle sample card: rect x=590, y=325, w=420, h=235
sample_lines = [
    "(the pmcarch sample:",
    "87,166,313 instructions",
    "over 96,163,187 cycles,",
    "BMR% 3.44, LLC% 73.45)"
]
for line in sample_lines:
    w = len(line) * 24 * 0.6
    print(f"Sample line: '{line}' ({len(line)} chars) -> width {w:.1f}px in 420px box (padding = {(420-w)/2:.1f}px)")
    assert (420 - w)/2 >= 16

# 3. Right zone advice box: rect x=1095, y=420, w=420, h=165
advice3_lines = [
    "Run fewer instructions:",
    "a better algorithm,",
    "vectorisation,",
    "compiler options"
]
for line in advice3_lines:
    w = len(line) * 24 * 0.6
    print(f"Advice3 line: '{line}' ({len(line)} chars) -> width {w:.1f}px in 420px box (padding = {(420-w)/2:.1f}px)")
    assert (420 - w)/2 >= 16

# 4. Callout: rect x=40, y=650, w=940, h=210
# text starts at x=145, ends before 960 (box ends at 980)
callout_lines = [
    "Utilisation counts every cycle that is not idle,",
    "including cycles spent waiting on memory, so a CPU",
    "at 100% busy is not necessarily 100% efficient"
]
for line in callout_lines:
    w = len(line) * 26 * 0.6
    pad_right = 980 - (145 + w)
    print(f"Callout line: '{line}' ({len(line)} chars) -> width {w:.1f}px (right margin = {pad_right:.1f}px)")
    assert pad_right >= 16

# 5. Footer: rect x=40, y=885, w=940, h=185
footer_lines = [
    "A training job whose host threads show",
    "high CPU use and low IPC is memory-bound on the host"
]
for line in footer_lines:
    w = len(line) * 26 * 0.6
    pad_right = 980 - (145 + w)
    print(f"Footer line: '{line}' ({len(line)} chars) -> width {w:.1f}px (right margin = {pad_right:.1f}px)")
    assert pad_right >= 16

# 6. Tool 1: rect x=1035, y=742, w=500, h=142
# text starts at x=1055 (left pad = 20)
# monospace char = 24 * 0.62 = 14.88
tool1_lines = [
    "perf stat -e cycles,",
    "instructions,cache-misses,",
    "context-switches,",
    "cpu-migrations ./prog"
]
for line in tool1_lines:
    w = len(line) * 24 * 0.62
    pad_right = (1035 + 500) - (1055 + w)
    print(f"Tool 1 line: '{line}' ({len(line)} chars) -> width {w:.1f}px (right pad = {pad_right:.1f}px)")
    assert pad_right >= 16

# 7. Tool 2: rect x=1035, y=904, w=500, h=142
tool2_lines = [
    "pmcarch prints K_CYCLES,",
    "K_INSTR, IPC, BR_RETIRED,",
    "BR_MISPRED, BMR%, LLCREF,",
    "LLCMISS, LLC%"
]
for line in tool2_lines:
    w = len(line) * 24 * 0.62
    pad_right = (1035 + 500) - (1055 + w)
    print(f"Tool 2 line: '{line}' ({len(line)} chars) -> width {w:.1f}px (right pad = {pad_right:.1f}px)")
    assert pad_right >= 16

print("\nALL PADDING AND LINE LENGTH CHECKS PASSED!")
