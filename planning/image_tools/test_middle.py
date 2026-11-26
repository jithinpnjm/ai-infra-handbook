from test_wrap import est_width

l3_lines = [
    [("iptables degrades", 28, False)],
    [("beyond roughly", 28, False)],
    [("5,000 Services", 28, False)],
    [("or 25,000", 28, False)],
    [("endpoints", 28, False)],
]
for idx, line in enumerate(l3_lines):
    w = est_width(line)
    print(f"Line {idx+1}: width={w:.1f}px, text={[t for t,fs,m in line]}")

