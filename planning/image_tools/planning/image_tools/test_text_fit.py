#!/usr/bin/env python3

def check_card1():
    text = "Fleet 400 GPUs, 320 in use, demand growing 8 percent a month, GPU lead time 3 months, headroom policy 20 percent"
    lines = [
        "Fleet 400 GPUs,",
        "320 in use, demand",
        "growing 8 percent",
        "a month, GPU lead",
        "time 3 months,",
        "headroom policy",
        "20 percent"
    ]
    reconstructed = " ".join(lines)
    assert reconstructed == text, f"Mismatch:\n{reconstructed}\nvs\n{text}"
    card_w = 340
    for l in lines:
        w = len(l) * 0.6 * 24
        pad = (card_w - w) / 2
        print(f"Card 1 line: '{l}' ({len(l)} chars), w={w:.1f}px, pad={pad:.1f}px")
        assert pad >= 16, f"Padding {pad} < 16 for line '{l}'"

def check_card2():
    text = "Demand after the lead time: 320 x 1.08 cubed = 403.1"
    lines = [
        "Demand after the",
        "lead time: 320 x",
        "1.08 cubed = 403.1"
    ]
    reconstructed = " ".join(lines)
    assert reconstructed == text, f"Mismatch:\n{reconstructed}\nvs\n{text}"
    card_w = 340
    for l in lines:
        w = len(l) * 0.6 * 24
        pad = (card_w - w) / 2
        print(f"Card 2 line: '{l}' ({len(l)} chars), w={w:.1f}px, pad={pad:.1f}px")
        assert pad >= 16, f"Padding {pad} < 16 for line '{l}'"

def check_card3():
    text = "GPUs needed with headroom: 403.1 x 1.2, rounded up = 484"
    lines = [
        "GPUs needed with",
        "headroom: 403.1",
        "x 1.2, rounded",
        "up = 484"
    ]
    reconstructed = " ".join(lines)
    assert reconstructed == text, f"Mismatch:\n{reconstructed}\nvs\n{text}"
    card_w = 340
    for l in lines:
        w = len(l) * 0.6 * 24
        pad = (card_w - w) / 2
        print(f"Card 3 line: '{l}' ({len(l)} chars), w={w:.1f}px, pad={pad:.1f}px")
        assert pad >= 16, f"Padding {pad} < 16 for line '{l}'"

def check_card4():
    text = "Order today: 484 - 400 = 84"
    lines = [
        "Order today:",
        "484 - 400 = 84"
    ]
    reconstructed = " ".join(lines)
    assert reconstructed == text, f"Mismatch:\n{reconstructed}\nvs\n{text}"
    card_w = 340
    for l in lines:
        w = len(l) * 0.6 * 28
        pad = (card_w - w) / 2
        print(f"Card 4 line: '{l}' ({len(l)} chars), w={w:.1f}px, pad={pad:.1f}px")
        assert pad >= 16, f"Padding {pad} < 16 for line '{l}'"

def check_contrast():
    text = "plan against lead time, not today's load: today's load tells you what is busy now, lead time tells you what you must order now"
    lines = [
        "plan against lead time, not today's load:",
        "today's load tells you what is busy now,",
        "lead time tells you what you must order now"
    ]
    reconstructed = " ".join(lines)
    assert reconstructed == text, f"Mismatch:\n{reconstructed}\nvs\n{text}"
    card_w = 940
    for l in lines:
        w = len(l) * 0.6 * 25
        pad = (card_w - w) / 2
        print(f"Contrast line: '{l}' ({len(l)} chars), w={w:.1f}px, pad={pad:.1f}px")
        assert pad >= 16, f"Padding {pad} < 16 for line '{l}'"

def check_curveball():
    text = "vendor delays 200 GPUs: redo the same chain"
    lines = [
        "vendor delays 200 GPUs:",
        "redo the same chain"
    ]
    reconstructed = " ".join(lines)
    assert reconstructed == text, f"Mismatch:\n{reconstructed}\nvs\n{text}"
    card_w = 520
    for l in lines:
        w = len(l) * 0.6 * 24
        pad = (card_w - w) / 2
        print(f"Curveball line: '{l}' ({len(l)} chars), w={w:.1f}px, pad={pad:.1f}px")
        assert pad >= 16, f"Padding {pad} < 16 for line '{l}'"

if __name__ == "__main__":
    check_card1()
    check_card2()
    check_card3()
    check_card4()
    check_contrast()
    check_curveball()
    print("ALL TEXT WRAPPING CHECKS PASSED!")
