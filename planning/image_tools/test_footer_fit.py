# Test 2x2 grid for footer test strip
row1 = [
    ("sudo systemctl start echo.socket", 24),
    ("ss -ltn | grep 22222", 24)
]
row2 = [
    ("echo hi | nc localhost 22222", 24),
    ("systemctl list-sockets", 24)
]

box_w = 710
for r_name, r in [("Row 1", row1), ("Row 2", row2)]:
    for cmd, fs in r:
        w = len(cmd) * fs * 0.62
        pad = (box_w - w) / 2
        print(f"[{r_name}] w={w:5.1f} / {box_w} (pad={pad:4.1f}) | '{cmd}'")
        assert pad >= 16
print("FOOTER 2x2 PASSES WITH HUGE PADDING!")
