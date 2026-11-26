#!/usr/bin/env python3

def test_bracket1_wrap():
    text = "lines 1-2: finding the link address because the client needs the server's MAC before it can send a frame"
    # Wrap into lines:
    lines = [
        "lines 1-2: finding the",
        "link address because",
        "the client needs the",
        "server's MAC before it",
        "can send a frame"
    ]
    reconstructed = " ".join(lines)
    assert reconstructed == text, f"Mismatch: '{reconstructed}' vs '{text}'"
    for l in lines:
        w = len(l) * 0.6 * 24
        print(f"'{l}': len={len(l)}, w={w:.1f}px")
        assert w <= 350, f"Line too wide: {w}"
    print("Bracket 1 lines all valid!")

test_bracket1_wrap()
