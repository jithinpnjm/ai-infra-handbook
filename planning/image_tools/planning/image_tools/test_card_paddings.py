#!/usr/bin/env python3
import xml.etree.ElementTree as ET

cards = [
    {
        "name": "Header Card",
        "box": (50, 85, 1500, 70),
        "icon": (75, 92, 56, 56),
        "text_x": 160,
        "text_y": 130,
        "fs": 30,
        "lines": ["Timeline for vllm-llama"]
    },
    {
        "name": "Left Note Card",
        "box": (75, 195, 660, 150),
        "icon": (95, 242, 56, 56),
        "text_x": 175,
        "text_y": 244,
        "fs": 26,
        "lines": [
            "during loading the server ",
            "downloads or maps weights and ",
            "captures CUDA graphs"
        ]
    },
    {
        "name": "Segment 1 startupProbe Card",
        "box": (75, 365, 660, 295),
        "icon": (95, 485, 56, 56),
        "text_x": 175,
        "text_y": 425,
        "fs": 26,
        "lines": [
            "startupProbe: periodSeconds 10, ",
            "failureThreshold 180, up to 30 ",
            "minutes; liveness and readiness ",
            "are disabled until it succeeds ",
            "once"
        ]
    },
    {
        "name": "Red Cross Failure Card",
        "box": (75, 680, 660, 230),
        "icon": (95, 767, 56, 56),
        "text_x": 175,
        "text_y": 750,
        "fs": 26,
        "lines": [
            "liveness with no startup probe ",
            "on a slow starter creates a ",
            "restart loop"
        ]
    },
    {
        "name": "Right Lane 1 readinessProbe Card",
        "box": (865, 210, 660, 320),
        "icon": (885, 342, 56, 56),
        "text_x": 965,
        "text_y": 300,
        "fs": 26,
        "lines": [
            "readinessProbe periodSeconds 5: ",
            "on failure the pod IP leaves the ",
            "EndpointSlices, container is NOT ",
            "restarted"
        ]
    },
    {
        "name": "Right Lane 2 livenessProbe Card",
        "box": (865, 560, 660, 320),
        "icon": (885, 692, 56, 56),
        "text_x": 965,
        "text_y": 650,
        "fs": 26,
        "lines": [
            "livenessProbe periodSeconds 20, ",
            "failureThreshold 6: restarts ",
            "only after 2 full minutes of no ",
            "response"
        ]
    },
    {
        "name": "Footer Bar",
        "box": (50, 960, 1500, 70),
        "icon": None,
        "text_x": 800, # centered
        "text_y": 1004,
        "fs": 28,
        "lines": ["Never tie liveness to dependencies"]
    }
]

print("=== CHECKING PADDINGS AND CLEARANCES ===")
for c in cards:
    bx, by, bw, bh = c["box"]
    fs = c["fs"]
    char_w = fs * 0.60
    
    print(f"\nCard: {c['name']}")
    print(f"  Box: x=[{bx}, {bx+bw}], y=[{by}, {by+bh}] (w={bw}, h={bh})")
    
    # Check left clearance from icon:
    if c["icon"]:
        ix, iy, iw, ih = c["icon"]
        icon_right = ix + iw
        text_left = c["text_x"]
        pad_icon = text_left - icon_right
        print(f"  Icon right={icon_right}, Text left={text_left} -> Gap = {pad_icon}px (>= 16px required)")
        assert pad_icon >= 16, f"Gap between icon and text {pad_icon} < 16px!"
    else:
        if c["text_x"] != 800:
            pad_left = c["text_x"] - bx
            assert pad_left >= 16
            
    # Check right clearance for every line:
    for i, ln in enumerate(c["lines"]):
        clean_ln = ln.strip()
        w = len(clean_ln) * char_w
        if c["text_x"] == 800: # centered
            text_right = 800 + w / 2
            text_left = 800 - w / 2
            pad_r = (bx + bw) - text_right
            pad_l = text_left - bx
            print(f"  Line {i+1}: '{clean_ln}' : len={len(clean_ln)}, w={w:.1f}px -> pad_l={pad_l:.1f}px, pad_r={pad_r:.1f}px")
            assert pad_l >= 16 and pad_r >= 16
        else:
            text_right = c["text_x"] + w
            box_right = bx + bw
            pad_r = box_right - text_right
            print(f"  Line {i+1}: '{clean_ln}' : len={len(clean_ln)}, w={w:.1f}px -> text_right={text_right:.1f}px, pad_r={pad_r:.1f}px (>= 16px required)")
            assert pad_r >= 16, f"Line '{clean_ln}' overflow! pad_r={pad_r} < 16px!"

    # Check vertical bounds:
    dy = 38 if len(c["lines"]) > 1 else 0
    top_text = c["text_y"] - fs * 0.85
    bot_text = c["text_y"] + (len(c["lines"]) - 1) * dy + fs * 0.25
    pad_top = top_text - by
    pad_bot = (by + bh) - bot_text
    print(f"  Vertical text: top={top_text:.1f}, bot={bot_text:.1f} -> pad_top={pad_top:.1f}px, pad_bot={pad_bot:.1f}px")
    assert pad_top >= 16, f"pad_top {pad_top} < 16px!"
    assert pad_bot >= 16, f"pad_bot {pad_bot} < 16px!"

print("\nALL BOX PADDINGS AND CLEARANCES EXCEED 16px REQUIREMENT! (PASS)")
