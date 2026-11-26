#!/usr/bin/env python3

def test_box2_wrapping():
    box_w = 600
    avail_w = box_w - 32
    
    l1 = [
        "2 perf script report",
        "flamegraph (perf 5.8 and newer)"
    ]
    l2 = [
        "perf script,",
        "stackcollapse-perf.pl,",
        "flamegraph.pl"
    ]
    
    for line in l1 + l2:
        w = len(line) * 24 * 0.62
        padding = (box_w - w) / 2
        print(f"'{line}': w={w:.1f}px, padding={padding:.1f}px (min 16 required)")
        assert padding >= 16

test_box2_wrapping()
