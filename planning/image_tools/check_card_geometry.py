#!/usr/bin/env python3

cards_and_texts = [
    {
        "card": "Card 1", "bx": 40, "by": 175, "bw": 270, "bh": 340,
        "text_x": 56, "text_y": 285, "fs": 24, "align": "left",
        "lines": [
            "pod passes its",
            "readiness check",
            "(Ready true;",
            "readiness gates",
            "satisfied)"
        ],
        "icon": {"x": 225, "y": 187, "w": 56, "h": 56},
        "circle": {"cx": 76, "cy": 208, "r": 24}
    },
    {
        "card": "Card 2", "bx": 350, "by": 175, "bw": 285, "bh": 340,
        "text_x": 366, "text_y": 280, "fs": 24, "align": "left",
        "lines": [
            "EndpointSlice",
            "controller adds",
            "the pod to a",
            "slice: conditions",
            "ready, serving,",
            "terminating"
        ],
        "icon": {"x": 555, "y": 187, "w": 56, "h": 56},
        "circle": {"cx": 386, "cy": 208, "r": 24}
    },
    {
        "card": "Card 3", "bx": 675, "by": 175, "bw": 245, "bh": 340,
        "text_x": 691, "text_y": 315, "fs": 24, "align": "left",
        "lines": [
            "API server",
            "publishes the",
            "change"
        ],
        "icon": {"x": 840, "y": 187, "w": 56, "h": 56},
        "circle": {"cx": 711, "cy": 208, "r": 24}
    },
    {
        "card": "Card 4", "bx": 960, "by": 175, "bw": 295, "bh": 340,
        "text_x": 976, "text_y": 280, "fs": 24, "align": "left",
        "lines": [
            "each node",
            "kube-proxy sees",
            "it and programs",
            "rules on its next",
            "sync (batch",
            "interval)"
        ],
        "icon": {"x": 1175, "y": 187, "w": 56, "h": 56},
        "circle": {"cx": 996, "cy": 208, "r": 24}
    },
    {
        "card": "Card 5", "bx": 1295, "by": 175, "bw": 265, "bh": 340,
        "text_x": 1311, "text_y": 325, "fs": 24, "align": "left",
        "lines": [
            "traffic reaches",
            "the pod"
        ],
        "icon": {"x": 1480, "y": 187, "w": 56, "h": 56},
        "circle": {"cx": 1331, "cy": 208, "r": 24}
    },
    {
        "card": "Box a", "bx": 40, "by": 565, "bw": 240, "bh": 300,
        "text_x": 160, "text_y": 700, "fs": 26, "align": "center",
        "lines": [
            "pod",
            "terminating"
        ],
        "icon": {"x": 132, "y": 585, "w": 56, "h": 56}
    },
    {
        "card": "Box b", "bx": 320, "by": 565, "bw": 350, "bh": 300,
        "text_x": 495, "text_y": 700, "fs": 24, "align": "center",
        "lines": [
            "slice shows ready",
            "false, serving true"
        ],
        "icon": {"x": 467, "y": 585, "w": 56, "h": 56}
    },
    {
        "card": "Box c", "bx": 710, "by": 565, "bw": 480, "bh": 300,
        "text_x": 950, "text_y": 690, "fs": 24, "align": "center",
        "lines": [
            "proxies keep serving it only",
            "if no ready endpoints remain",
            "(graceful drain)"
        ],
        "icon": {"x": 922, "y": 585, "w": 56, "h": 56}
    },
    {
        "card": "Box d", "bx": 1230, "by": 565, "bw": 330, "bh": 300,
        "text_x": 1395, "text_y": 700, "fs": 26, "align": "center",
        "lines": [
            "removal races",
            "SIGTERM"
        ],
        "icon": {"x": 1367, "y": 585, "w": 56, "h": 56}
    },
    {
        "card": "Side Box", "bx": 40, "by": 915, "bw": 1040, "bh": 245,
        "text_x": 145, "text_y": 968, "fs": 24, "align": "left",
        "lines": [
            "a Service with no ready endpoints:",
            "iptables REJECT sends ICMP port unreachable,",
            "client sees connection refused immediately;",
            "empty kubectl get endpointslices",
            "means selector mismatch or unready pods"
        ],
        "icon": {"x": 68, "y": 955, "w": 56, "h": 56}
    },
    {
        "card": "Fix Box", "bx": 1120, "by": 915, "bw": 440, "bh": 245,
        "text_x": 1340, "text_y": 1042, "fs": 24, "align": "center",
        "lines": [
            "preStop sleep plus",
            "graceful shutdown (5.7)"
        ],
        "icon": {"x": 1312, "y": 938, "w": 56, "h": 56}
    }
]

print("Checking text paddings and boundaries...")
for item in cards_and_texts:
    name = item["card"]
    bx, by, bw, bh = item["bx"], item["by"], item["bw"], item["bh"]
    tx, ty, fs = item["text_x"], item["text_y"], item["fs"]
    char_w = 0.6 * fs
    align = item["align"]
    
    # Check lines
    for i, line in enumerate(item["lines"]):
        lw = len(line) * char_w
        if align == "left":
            lx0 = tx
            lx1 = tx + lw
        else: # center
            lx0 = tx - lw / 2
            lx1 = tx + lw / 2
        
        left_pad = lx0 - bx
        right_pad = (bx + bw) - lx1
        assert left_pad >= 16, f"[{name}] line {i} '{line}' left pad {left_pad:.1f} < 16!"
        assert right_pad >= 16, f"[{name}] line {i} '{line}' right pad {right_pad:.1f} < 16!"
    
    # Check top pad to icon/circle
    if "circle" in item:
        bottom_circle = item["circle"]["cy"] + item["circle"]["r"]
        top_text = ty - fs
        pad_top = top_text - bottom_circle
        assert pad_top >= 16, f"[{name}] top pad to circle {pad_top:.1f} < 16!"
    
    if "icon" in item:
        # If icon is directly above text
        icon = item["icon"]
        if icon["x"] >= bx and (icon["x"] + icon["w"]) <= (bx + bw):
            if icon["y"] < ty:
                bottom_icon = icon["y"] + icon["h"]
                # Only if icon is horizontally overlapping text
                top_text = ty - fs
                # check if icon is vertically above text
                if align == "center":
                    pad_top = top_text - bottom_icon
                    assert pad_top >= 16, f"[{name}] top pad to icon {pad_top:.1f} < 16!"

    print(f"[{name}] OK! All lines fit with >= 16px padding on all sides.")

print("\nALL CARD PADDING CHECKS PASSED!")
