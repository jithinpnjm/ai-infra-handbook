#!/usr/bin/env python3

text = "lines 1-2: finding the link address because the client needs the server's MAC before it can send a frame"

# If box width is 380px, available width for text with 20px padding is 340px.
# 340 / 14.4 = 23.6 characters max per line.

def test_wrap(n_lines):
    # Try 5 lines:
    lines5 = [
        "lines 1-2: finding the ",
        "link address because ",
        "the client needs the ",
        "server's MAC before it ",
        "can send a frame"
    ]
    reconstructed = "".join(lines5).strip()
    assert reconstructed == text, f"'{reconstructed}' != '{text}'"
    print("5 lines wrap:")
    for l in lines5:
        w = len(l) * 0.6 * 24
        print(f"  '{l}': {len(l)} chars, {w:.1f}px")

test_wrap(5)
