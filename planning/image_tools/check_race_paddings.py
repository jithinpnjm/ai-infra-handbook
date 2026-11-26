import xml.etree.ElementTree as ET

checks = [
    ("Pod resolver header", 50, 95, 380, 110, [
        ("Pod resolver", 32, False, 260, 162, "middle")
    ]),
    ("Pod parallel port note", 50, 235, 380, 85, [
        ("in parallel from the", 24, False, 240, 270, "middle"),
        ("same UDP source port", 24, False, 240, 300, "middle")
    ]),
    ("Pod waits card", 50, 475, 380, 115, [
        ("Pod waits 1 s or 5 s", 24, False, 255, 525, "middle"),
        ("then retries", 24, False, 255, 557, "middle")
    ]),
    ("Both reach node card", 885, 115, 640, 125, [
        ("Both reach the node;", 24, False, 1245, 152, "middle"),
        ("the kernel must insert the", 24, False, 1245, 182, "middle"),
        ("DNAT conntrack entry for each", 24, False, 1245, 212, "middle")
    ]),
    ("Guest book card", 885, 255, 640, 115, [
        ("two people sign the same guest", 24, False, 1245, 297, "middle"),
        ("book at the same instant", 24, False, 1245, 329, "middle")
    ]),
    ("Lost packet card", 885, 385, 640, 215, [
        ("one packet loses the insertion,", 26, False, 1245, 480, "middle"),
        ("a reply is lost", 26, False, 1245, 516, "middle")
    ]),
    ("Normal bar label", 160, 648, 1360, 54, [
        ("normal reply in milliseconds", 24, False, 370, 683, "start")
    ]),
    ("Delay bar label", 160, 715, 1360, 54, [
        ("delay of 1 s or 5 s", 24, False, 370, 750, "start")
    ]),
    ("Mitigations box", 160, 818, 1360, 124, [
        ("single-request-reopen in resolv.conf options, use TCP for DNS,", 25, False, 840, 870, "middle"),
        ("NodeLocal DNSCache, newer kernels fix it", 25, False, 840, 906, "middle")
    ]),
    ("Related box", 160, 998, 1360, 134, [
        ("stale UDP conntrack entries can keep sending to a deleted backend until timeout;", 24, False, 840, 1052, "middle"),
        ("check conntrack -L -p udp | grep svc", 24, False, 840, 1088, "middle")
    ])
]

print("=== CHECKING PADDINGS AND WIDTHS ===")
for name, bx, by, bw, bh, lines in checks:
    print(f"\nBox: {name} [x={bx}, y={by}, w={bw}, h={bh}]")
    for line, fs, is_mono, tx, ty, anchor in lines:
        coeff = 0.62 if is_mono else 0.6
        if "resolv.conf" in line or "conntrack" in line: coeff = 0.62
        est_w = len(line) * coeff * fs
        if anchor == "middle":
            x_min = tx - est_w / 2
            x_max = tx + est_w / 2
        elif anchor == "start":
            x_min = tx
            x_max = tx + est_w
        else:
            x_min = tx - est_w
            x_max = tx

        left_pad = x_min - bx
        right_pad = (bx + bw) - x_max
        top_pad = (ty - fs) - by
        bot_pad = (by + bh) - ty

        print(f"  Line: '{line}' ({len(line)} ch, est_w={est_w:.1f}px)")
        print(f"    Left pad: {left_pad:.1f}px, Right pad: {right_pad:.1f}px")
        print(f"    Top pad: {top_pad:.1f}px, Bot pad: {bot_pad:.1f}px")

        assert left_pad >= 16, f"Left padding {left_pad} < 16 on '{line}'!"
        assert right_pad >= 16, f"Right padding {right_pad} < 16 on '{line}'!"
        assert top_pad >= 10, f"Top padding {top_pad} < 10 on '{line}'!"
        assert bot_pad >= 10, f"Bottom padding {bot_pad} < 10 on '{line}'!"

print("\nALL PADDING CHECKS PASSED (>= 16px horizontally, >= 10px vertically)!")
