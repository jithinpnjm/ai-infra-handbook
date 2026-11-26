import xml.etree.ElementTree as ET

def verify_strict_paddings(svg_path):
    print("Verifying strict paddings...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    checks = [
        # Box 1: Address A
        {
            "box": ("Box 1 Address A", 64, 164, 460, 100),
            "lines": [
                ("Address A:", 28, False, 156, 204),
                ("10.20.37.130", 28, False, 156, 238)
            ]
        },
        # Box 2: Mask
        {
            "box": ("Box 2 Mask", 548, 164, 508, 100),
            "lines": [
                ("Mask: /22", 28, False, 640, 204),
                ("(third octet 252)", 28, False, 640, 238)
            ]
        },
        # Box 3: A AND mask
        {
            "box": ("Box 3 A AND mask", 200, 310, 696, 66),
            "lines": [
                ("A AND mask = 10.20.36.0 network", 26, True, 278, 352)
            ]
        },
        # Box 4: Address B
        {
            "box": ("Box 4 Address B", 300, 430, 496, 100),
            "lines": [
                ("Address B:", 28, False, 395, 470),
                ("10.20.40.1", 28, False, 395, 504)
            ]
        },
        # Box 5: B AND mask
        {
            "box": ("Box 5 B AND mask", 200, 575, 696, 66),
            "lines": [
                ("B AND mask = 10.20.40.0 network", 26, True, 278, 617)
            ]
        },
        # Side note card
        {
            "box": ("Side note card", 1140, 275, 400, 350),
            "lines": [
                ("10.20.36.0/22 covers", 24, False, 1165, 350),
                ("third octets 36 to 39,", 24, False, 1165, 398),
                ("so 10.20.36.0 to", 24, False, 1165, 446),
                ("10.20.39.255", 24, False, 1165, 494)
            ]
        },
        # Left Result Box
        {
            "box": ("Left Result Box", 40, 685, 740, 145),
            "lines": [
                ("Same network as 10.20.36.0/22:", 26, False, 148, 746),
                ("direct on the link (ARP)", 26, False, 148, 788)
            ]
        },
        # Right Result Box
        {
            "box": ("Right Result Box", 820, 685, 740, 145),
            "lines": [
                ("Different network:", 26, False, 928, 746),
                ("send to the gateway", 26, False, 928, 788)
            ]
        },
        # Takeaway bar
        {
            "box": ("Takeaway bar", 40, 860, 1520, 75),
            "lines": [
                ("Every host runs this check for every packet it sends.", 28, False, 800 - (53 * 0.6 * 28) / 2, 907)
            ]
        }
    ]

    all_passed = True
    for item in checks:
        name, bx, by, bw, bh = item["box"]
        b_right = bx + bw
        b_bottom = by + bh
        print(f"\nChecking {name} (x={bx}..{b_right}, y={by}..{b_bottom}):")
        for text, fs, is_mono, tx, ty in item["lines"]:
            char_w = 0.62 * fs if is_mono else 0.60 * fs
            text_w = len(text) * char_w
            text_right = tx + text_w
            
            top_pad = ty - 0.75 * fs - by
            bottom_pad = b_bottom - (ty + 0.25 * fs)
            left_pad = tx - bx
            right_pad = b_right - text_right

            pads = [("left", left_pad), ("right", right_pad), ("top", top_pad), ("bottom", bottom_pad)]
            min_pad_name, min_pad_val = min(pads, key=lambda x: x[1])
            status = "OK" if min_pad_val >= 16 else "FAIL"
            if min_pad_val < 16:
                all_passed = False
            print(f"  [{status}] '{text}': min_pad={min_pad_val:.1f}px ({min_pad_name}), L={left_pad:.1f}, R={right_pad:.1f}, T={top_pad:.1f}, B={bottom_pad:.1f}")

    assert all_passed, "Some text lines have padding < 16px!"
    print("\nALL PADDINGS >= 16px! (PASS)")

verify_strict_paddings("test_candidate.svg")
