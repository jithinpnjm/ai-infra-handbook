#!/usr/bin/env python3

def test_wrapping():
    box_w = 670
    pad = 24
    avail_w = box_w - 2 * pad
    fs = 24
    char_w = 0.6 * fs # 14.4

    print(f"Available width: {avail_w} px. Max characters per line: {avail_w / char_w:.1f}")

    lines_l3 = [
        "Cluster Autoscaler orders from a fixed",
        "menu of node groups, each with one shape"
    ]
    for l in lines_l3:
        w = len(l) * char_w
        print(f"L3 line ({len(l)} chars): {w:.1f} px <= {avail_w} px (fits: {w <= avail_w})")

    lines_l4 = [
        "Karpenter watches Pending pods, batches them,",
        "computes the best set of instance types that",
        "satisfy their constraints, and provisions just",
        "in time; bin-packing, spot handling with",
        "interruption notices, automatic rotation and",
        "drift correction"
    ]
    print("\n--- Label 4 ---")
    for l in lines_l4:
        w = len(l) * char_w
        print(f"L4 line ({len(l)} chars): {w:.1f} px <= {avail_w} px (fits: {w <= avail_w})")
    assert " ".join(lines_l4) == "Karpenter watches Pending pods, batches them, computes the best set of instance types that satisfy their constraints, and provisions just in time; bin-packing, spot handling with interruption notices, automatic rotation and drift correction"
    print("Label 4 exact match verified!")

test_wrapping()
