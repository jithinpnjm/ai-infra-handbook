#!/usr/bin/env python3

def test_card(name, lines, card_w=500, fs=24):
    print(f"=== {name} ({len(lines)} lines) ===")
    max_w = 0
    for l in lines:
        w = len(l) * 0.6 * fs
        if w > max_w:
            max_w = w
        pad = (card_w - w) / 2
        print(f"  w={w:5.1f}px (len={len(l):2d}) | pad={pad:4.1f}px | '{l}'")
    assert card_w - max_w >= 32, f"Overflow in {name}! max_w={max_w}, avail={card_w - 32}"
    print(f"PASS: {name} min horizontal padding = {(card_w - max_w)/2:.1f}px >= 16px\n")

card3_lines = [
    "AWS supports 9001 inside a VPC",
    "but only 1500 across the",
    "Internet and on many",
    "inter-region and VPN paths:",
    "validate jumbo designs",
    "path by path"
]
assert " ".join(card3_lines) == "AWS supports 9001 inside a VPC but only 1500 across the Internet and on many inter-region and VPN paths: validate jumbo designs path by path"
test_card("Card 3 (AWS)", card3_lines)
