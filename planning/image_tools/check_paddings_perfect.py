# Paddings test for golden_perfect.svg
boxes = {
    "Golden signals": {
        "box": (570, 92, 460, 74),
        "lines": [("Golden signals", 32, 670, 141)]
    },
    "RED container": {
        "box": (60, 235, 710, 605),
        "lines": [
            ("RED: service health", 28, 155, 278),
            ("(user view)", 28, 155, 312)
        ]
    },
    "Latency": {
        "box": (90, 330, 530, 130),
        "lines": [
            ("Latency (duration,", 28, 185, 385),
            ("use percentiles)", 28, 185, 421)
        ]
    },
    "Traffic": {
        "box": (90, 495, 530, 130),
        "lines": [
            ("Traffic", 28, 185, 555),
            ("(request rate)", 28, 185, 591)
        ]
    },
    "Errors": {
        "box": (90, 660, 530, 130),
        "lines": [
            ("Errors", 28, 185, 720),
            ("(request errors)", 28, 185, 756)
        ]
    },
    "USE container": {
        "box": (830, 235, 710, 605),
        "lines": [
            ("USE: machine health", 28, 925, 278),
            ("(host view)", 28, 925, 312)
        ]
    },
    "Saturation": {
        "box": (860, 330, 650, 130),
        "lines": [("Saturation (USE)", 30, 965, 410)]
    },
    "Netflix example": {
        "box": (860, 485, 650, 180),
        "lines": [
            ("Netflix example: saturation", 25, 965, 538),
            ("approximated by the gap between", 25, 965, 572),
            ("p99 latency and the average", 25, 965, 606)
        ]
    },
    "Dashed note": {
        "box": (860, 690, 650, 115),
        "lines": [
            ("Utilisation and errors", 26, 965, 747),
            ("also live here", 26, 965, 781)
        ]
    },
    "Takeaway bar": {
        "box": (60, 870, 1480, 64),
        "lines": [("RED judges the service, USE judges the host.", 28, 800 - 0.5 * len("RED judges the service, USE judges the host.") * 0.6 * 28, 911)]
    }
}

print("Checking paddings for golden_perfect.svg:")
all_pass = True
for name, data in boxes.items():
    bx, by, bw, bh = data["box"]
    for text, fs, tx, ty in data["lines"]:
        tw = len(text) * 0.6 * fs
        th = fs * 0.8
        left_pad = tx - bx
        right_pad = (bx + bw) - (tx + tw)
        top_pad = (ty - th) - by
        bottom_pad = (by + bh) - ty
        
        ok = left_pad >= 16 and right_pad >= 16 and top_pad >= 14 and bottom_pad >= 14
        if not ok:
            all_pass = False
        print(f"[{'PASS' if ok else 'FAIL'}] {name} - '{text}':")
        print(f"       left={left_pad:.1f}px, right={right_pad:.1f}px, top={top_pad:.1f}px, bottom={bottom_pad:.1f}px")

assert all_pass, "Some paddings failed!"
print("\nAll paddings >= 16px! (PASS)")
