#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Check our SVG with exact calculations

# Box 1: Requests per second
# Box: (40, 130, 350, 420)
# Icon: center cx=215, cy=175, r=24 -> y from 151 to 199
# Text: centered at 215, y=246
b1 = {
    "name": "Fence 1: Requests per second",
    "box": (40, 130, 350, 420),
    "icon_bottom": 199,
    "center_x": 215,
    "lines": [
        ("Requests", 30, 246),
        ("per second:", 30, 246 + 36),
        ("protects gateway,", 24, 246 + 36 + 42),
        ("tokenizer, scheduler;", 24, 246 + 36 + 42 + 32),
        ("unit requests;", 24, 246 + 36 + 42 + 32 + 40),
        ("missing:", 24, 246 + 36 + 42 + 32 + 40 + 40),
        ("connection floods", 24, 246 + 36 + 42 + 32 + 40 + 40 + 32)
    ]
}

# Box 2: Tokens per second
b2 = {
    "name": "Fence 2: Tokens per second",
    "box": (430, 130, 350, 420),
    "icon_bottom": 199,
    "center_x": 605,
    "lines": [
        ("Tokens", 30, 246),
        ("per second:", 30, 246 + 36),
        ("protects GPU compute", 24, 246 + 36 + 38),
        ("and KV cache;", 24, 246 + 36 + 38 + 32),
        ("unit prompt plus", 24, 246 + 36 + 38 + 32 + 38),
        ("output tokens;", 24, 246 + 36 + 38 + 32 + 38 + 32),
        ("missing: one tenant", 24, 246 + 36 + 38 + 32 + 38 + 32 + 38),
        ("starves the rest", 24, 246 + 36 + 38 + 32 + 38 + 32 + 38 + 32)
    ]
}

# Box 3: Concurrent streams
b3 = {
    "name": "Fence 3: Concurrent streams",
    "box": (820, 130, 350, 420),
    "icon_bottom": 200,
    "center_x": 995,
    "lines": [
        ("Concurrent", 30, 246),
        ("streams:", 30, 246 + 36),
        ("protects open", 24, 246 + 36 + 38),
        ("connections and", 24, 246 + 36 + 38 + 32),
        ("decode slots;", 24, 246 + 36 + 38 + 32 + 32),
        ("unit streams;", 24, 246 + 36 + 38 + 32 + 32 + 38),
        ("missing: decode", 24, 246 + 36 + 38 + 32 + 32 + 38 + 38),
        ("queues overrun", 24, 246 + 36 + 38 + 32 + 32 + 38 + 38 + 32)
    ]
}

# Box 4: Daily or monthly quota
b4 = {
    "name": "Fence 4: Daily or monthly quota",
    "box": (1210, 130, 350, 420),
    "icon_bottom": 198,
    "center_x": 1385,
    "lines": [
        ("Daily or", 30, 246),
        ("monthly quota:", 30, 246 + 36),
        ("protects the bill", 24, 246 + 36 + 42),
        ("and the contract;", 24, 246 + 36 + 42 + 32),
        ("unit tokens;", 24, 246 + 36 + 42 + 32 + 40),
        ("missing:", 24, 246 + 36 + 42 + 32 + 40 + 40),
        ("surprise cost", 24, 246 + 36 + 42 + 32 + 40 + 40 + 32)
    ]
}

# Mechanism strip
b5 = {
    "name": "Mechanism strip: token bucket",
    "box": (40, 595, 1520, 290),
    "icon_box": (82, 714, 36, 56), # bucket icon
    "text_x": 150,
    "lines": [
        ("token bucket: a jar that starts full, is spent per request, refills slowly,", 24, 642),
        ("and allows bursts up to bucket size; charge prompt tokens plus max output", 24, 642 + 38),
        ("tokens at admission, refund the unused at the end; reject at once what can", 24, 642 + 38*2),
        ("never fit; a refused request must not burn a request slot; distributed", 24, 642 + 38*3),
        ("choice: shared store such as Redis is exact but adds a hop and a", 24, 642 + 38*4),
        ("dependency, local buckets are fast and slightly loose", 24, 642 + 38*5)
    ]
}

# Incident callout
b6 = {
    "name": "Incident callout",
    "box": (40, 930, 1520, 150),
    "icon_box": (74, 975, 52, 50), # alert icon
    "text_x": 150,
    "lines": [
        ("ten requests with 8,000 prompt tokens and a large max output made every", 24, 990),
        ("other tenant TTFT double while a requests-per-minute limit saw nothing wrong", 24, 990 + 42)
    ]
}

cards = [b1, b2, b3, b4, b5, b6]

print("=== CHECKING PADDINGS AND CLEARANCES ===")
for c in cards:
    bx, by, bw, bh = c["box"]
    print(f"\nChecking {c['name']}:")
    print(f"  Box: x=[{bx}, {bx+bw}], y=[{by}, {by+bh}]")

    if "center_x" in c:
        cx = c["center_x"]
        # Check icon clearance
        first_y = c["lines"][0][2]
        first_fs = c["lines"][0][1]
        top_text_y = first_y - first_fs * 0.85
        icon_gap = top_text_y - c["icon_bottom"]
        print(f"  Icon bottom={c['icon_bottom']}, First text top={top_text_y:.1f} -> Gap = {icon_gap:.1f}px (>= 16px)")
        assert icon_gap >= 16, f"Icon gap {icon_gap} < 16px!"

        for ln, fs, y in c["lines"]:
            w = len(ln) * fs * 0.6
            left = cx - w / 2
            right = cx + w / 2
            pad_l = left - bx
            pad_r = (bx + bw) - right
            print(f"    Line: '{ln}' (fs={fs}) -> w={w:.1f}px, pad_l={pad_l:.1f}px, pad_r={pad_r:.1f}px")
            assert pad_l >= 16, f"pad_l {pad_l} < 16px!"
            assert pad_r >= 16, f"pad_r {pad_r} < 16px!"

        last_y = c["lines"][-1][2]
        last_fs = c["lines"][-1][1]
        bot_text_y = last_y + last_fs * 0.25
        pad_bot = (by + bh) - bot_text_y
        print(f"  Bottom clearance: bot_text={bot_text_y:.1f}, box_bottom={by+bh} -> pad_bot={pad_bot:.1f}px (>= 16px)")
        assert pad_bot >= 16, f"pad_bot {pad_bot} < 16px!"

    else:
        # Left-aligned cards
        ix, iy, iw, ih = c["icon_box"]
        icon_right = ix + iw
        text_left = c["text_x"]
        pad_icon = text_left - icon_right
        print(f"  Icon right={icon_right}, Text left={text_left} -> Gap = {pad_icon}px (>= 16px)")
        assert pad_icon >= 16, f"Gap from icon {pad_icon} < 16px!"

        first_y = c["lines"][0][2]
        first_fs = c["lines"][0][1]
        top_text_y = first_y - first_fs * 0.85
        pad_top = top_text_y - by
        print(f"  Top clearance: top_text={top_text_y:.1f}, box_top={by} -> pad_top={pad_top:.1f}px (>= 16px)")
        assert pad_top >= 16, f"pad_top {pad_top} < 16px!"

        for ln, fs, y in c["lines"]:
            w = len(ln) * fs * 0.6
            text_right = text_left + w
            pad_r = (bx + bw) - text_right
            print(f"    Line: '{ln[:35]}...' -> w={w:.1f}px, pad_r={pad_r:.1f}px")
            assert pad_r >= 16, f"pad_r {pad_r} < 16px!"

        last_y = c["lines"][-1][2]
        last_fs = c["lines"][-1][1]
        bot_text_y = last_y + last_fs * 0.25
        pad_bot = (by + bh) - bot_text_y
        print(f"  Bottom clearance: bot_text={bot_text_y:.1f}, box_bottom={by+bh} -> pad_bot={pad_bot:.1f}px (>= 16px)")
        assert pad_bot >= 16, f"pad_bot {pad_bot} < 16px!"

print("\nALL CLEARANCES AND PADDINGS EXCEED 16px BY A HEALTHY MARGIN! (PASS)")
