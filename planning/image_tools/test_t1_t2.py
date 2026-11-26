#!/usr/bin/env python3

def test_t1_t2():
    # T1 step 1
    t1_s1_lines = [
        "PID 1 has no",
        "default action,",
        "so with no",
        "handler the",
        "signal is",
        "ignored"
    ]
    box_w = 285
    for l in t1_s1_lines:
        w = len(l) * 24 * 0.6
        pad = (box_w - w) / 2
        print(f"T1 S1: '{l}' w={w:.1f} pad={pad:.1f}")
        assert pad >= 16

    # T1 step 4
    t1_s4_lines = [
        "training job",
        "loses its",
        "chance to",
        "checkpoint"
    ]
    box_w = 280
    for l in t1_s4_lines:
        w = len(l) * 24 * 0.6
        pad = (box_w - w) / 2
        print(f"T1 S4: '{l}' w={w:.1f} pad={pad:.1f}")
        assert pad >= 16

    # T2 step 2
    l = "checkpoint written"
    w = len(l) * 28 * 0.6
    pad = (360 - w) / 2
    print(f"T2 S2: '{l}' w={w:.1f} pad={pad:.1f}")
    assert pad >= 16

test_t1_t2()
print("All passed!")
