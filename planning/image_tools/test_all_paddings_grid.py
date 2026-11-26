col1_l = 40
col1_r = 480
col1_w = col1_r - col1_l # 440 px
text_x = 172

causes_lines = [
    ["Data blocks ", "exhausted"],
    ["Inodes exhausted"],
    ["Mounted ", "read-only"],
    ["Quota reached"],
    ["Wrong place, ", "not mounted"],
    ["Deleted files ", "still open"],
    ["Reserved blocks ", "for root"]
]

for i, lines in enumerate(causes_lines, 1):
    for line in lines:
        w = len(line) * 30 * 0.6
        r = text_x + w
        pad_r = col1_r - r
        print(f"Cause {i}: '{line}' w={w:.1f} pad_r={pad_r:.1f}")
        assert pad_r >= 16.0, f"Cause {i} line '{line}' failed pad_r: {pad_r}"

print("All causes passed!")
