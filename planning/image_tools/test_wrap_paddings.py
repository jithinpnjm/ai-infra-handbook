col3_w = 585
fixes_splits = [
    # Row 1
    ["Delete or move data; ", "grow the filesystem"],
    # Row 2
    ["Delete files; recreate ", "with more inodes; ", "prefer XFS or bundled shards"],
    # Row 3
    ["Find the I/O error cause; ", "repair; remount"],
    # Row 4
    ["Raise the quota or clean up"],
    # Row 5
    ["Mount it properly; ", "move the stray data"],
    # Row 6
    ["Restart the holder, or truncate ", "through /proc/PID/fd/N"],
    # Row 7
    ["Lower the reservation ", "on data disks"]
]

for i, lines in enumerate(fixes_splits, 1):
    for line in lines:
        est_w = len(line) * 24 * 0.6
        pad = (col3_w - est_w) / 2
        print(f"Row {i} Fix: '{line}' len={len(line)} est_w={est_w:.1f} pad={pad:.1f}")
        assert pad >= 16.0, f"Padding {pad} < 16 for line: {line}"
print("All fix lines have >= 16px padding!")
