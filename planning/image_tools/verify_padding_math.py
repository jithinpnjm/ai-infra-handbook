#!/usr/bin/env python3

# Precise padding calculator for each text line and box

items = [
    {
        "box": "Teams",
        "bx": 60, "by": 140, "bw": 420, "bh": 150,
        "icon_top": 158, "icon_bot": 208,
        "lines": [("Teams", 32, 254)]
    },
    {
        "box": "Node health feed",
        "bx": 590, "by": 140, "bw": 420, "bh": 150,
        "icon_top": 158, "icon_bot": 202,
        "lines": [("Node health feed", 30, 252)]
    },
    {
        "box": "Queue and fair share",
        "bx": 60, "by": 380, "bw": 420, "bh": 180,
        "icon_top": 398, "icon_bot": 440,
        "lines": [("Queue and", 30, 484), ("fair share", 30, 524)]
    },
    {
        "box": "Topology-aware placer",
        "bx": 590, "by": 380, "bw": 420, "bh": 180,
        "icon_top": 398, "icon_bot": 444,
        "lines": [("Topology-aware", 30, 484), ("placer", 30, 524)]
    },
    {
        "box": "Nodes in fabric blocks",
        "bx": 1120, "by": 380, "bw": 420, "bh": 180,
        "icon_top": 398, "icon_bot": 442,
        "lines": [("Nodes in", 30, 484), ("fabric blocks", 30, 524)]
    },
    {
        "box": "Checkpoint store",
        "bx": 1120, "by": 650, "bw": 420, "bh": 150,
        "icon_top": 668, "icon_bot": 716,
        "lines": [("Checkpoint store", 30, 760)]
    },
]

all_ok = True
for it in items:
    bx, by, bw, bh = it["bx"], it["by"], it["bw"], it["bh"]
    cx = bx + bw / 2
    print(f"\n--- Box: {it['box']} (x={bx}, y={by}, w={bw}, h={bh}) ---")
    
    # Check icon padding
    itop = it["icon_top"] - by
    print(f"  Icon top pad: {itop} px (>=16: {itop >= 16})")
    assert itop >= 16
    
    # Check text lines
    first_ty = it["lines"][0][2]
    gap_icon_text = (first_ty - 30 * 0.8) - it["icon_bot"]
    print(f"  Gap icon-text: {gap_icon_text:.1f} px (>=16: {gap_icon_text >= 16})")
    assert gap_icon_text >= 16
    
    for text, fs, ty in it["lines"]:
        tw = len(text) * 0.6 * fs
        pad_x = (bw - tw) / 2
        pad_top = (ty - fs * 0.8) - by
        pad_bot = (by + bh) - ty
        print(f"  Line '{text}': w={tw:.1f}, pad_x={pad_x:.1f}, pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f}")
        if pad_x < 16 or pad_top < 16 or pad_bot < 16:
            print(f"  FAILED PADDING on line '{text}'")
            all_ok = False

last_ty = items[-1]["lines"][-1][2]
assert all_ok
print("\nALL BOXES AND TEXT PADDING VERIFIED >= 16 PX!")
