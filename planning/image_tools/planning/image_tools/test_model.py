#!/usr/bin/env python3

def test_complete_model():
    # Let's verify every single text line in every box
    boxes = {
        # Section 1 container (x=40, y=125, w=1520, h=200)
        "format_line": {
            "box": (40, 125, 1520, 200),
            "lines": [("name-version-pythontag-abitag-platformtag", "mono", 24, 800, 162)] # top = 162-24=138, pad_t = 138-125 = 13!
            # If y = 165: top = 165 - 24 = 141, pad_t = 141 - 125 = 16.0!
        }
    }
    print("Testing complete model...")

test_complete_model()
