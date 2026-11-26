causes_splits = [
    ["Data blocks ", "exhausted"],
    ["Inodes ", "exhausted"],
    ["Mounted ", "read-only"],
    ["Quota ", "reached"],
    ["Wrong place, ", "not mounted"],
    ["Deleted files ", "still open"],
    ["Reserved blocks ", "for root"]
]

col1_start = 40
col1_end = 495
text_x = 176

for i, lines in enumerate(causes_splits, 1):
    for line in lines:
        w = len(line) * 30 * 0.6
        r_edge = text_x + w
        r_pad = col1_end - r_edge
        print(f"Row {i} Cause line '{line}' len={len(line)} w={w:.1f} r_pad={r_pad:.1f}")
        assert r_pad >= 16.0, f"r_pad {r_pad} < 16 for line {line}"

print("All cause lines pass padding check!")
