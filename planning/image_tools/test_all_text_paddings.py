import xml.etree.ElementTree as ET
import re

# Font estimation functions
def text_width(text, font_family, font_size):
    rate = 0.62 if font_family == "monospace" else 0.60
    return len(text) * rate * font_size

def font_height_bounds(baseline_y, font_size):
    # Cap-height / ascent approx 0.75 * font_size
    # Descent approx 0.22 * font_size
    ascent = 0.75 * font_size
    descent = 0.22 * font_size
    top = baseline_y - ascent
    bottom = baseline_y + descent
    return top, bottom

# Let's test all text elements and boxes in our planned layout
cards = [
    {
        "id": "Subtitle Pill",
        "box": (450, 72, 700, 58), # x, y, w, h
        "font_family": "sans-serif", "font_size": 24,
        "lines": [("toy numbers chosen to show the mechanism", 800, 108, "center")]
    },
    {
        "id": "Setup Box",
        "box": (50, 170, 1500, 96), # x, y, w, h
        "icon": (75, 185, 56, 56),
        "font_family": "sans-serif", "font_size": 24,
        "lines": [
            ("Setup: eight replicas, forty prefixes, one hot prefix with 40 percent of traffic,", 155, 210, "left"),
            ("cache of six prefixes per replica, hit costs 0.10 s and miss 0.50 s", 155, 244, "left")
        ]
    },
    {
        "id": "Table 1 Header",
        "box": (66, 310, 1468, 54),
        "icon": (75, 309, 56, 56),
        "font_family": "sans-serif", "font_size": 30,
        "lines": [("Table 1 policy: hit rate, p50 s, p99 s, max over mean load", 155, 347, "left")]
    },
    {
        "id": "T1 Row 1",
        "box": (66, 372, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("round_robin 0.46, 0.50, 2.33, 1.00", 86, 404, "left")]
    },
    {
        "id": "T1 Row 2",
        "box": (66, 426, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("least_loaded 0.46, 0.50, 1.22, 1.16", 86, 458, "left")]
    },
    {
        "id": "T1 Row 3",
        "box": (66, 480, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("cache_only 0.98, 0.16, 4.39, 3.80", 86, 512, "left")]
    },
    {
        "id": "T1 Row 4",
        "box": (66, 534, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("cache_bounded 0.95, 0.10, 0.50, 2.13", 86, 566, "left")]
    },
    {
        "id": "Table 2 Header",
        "box": (66, 638, 1468, 54),
        "icon": (75, 637, 56, 56),
        "font_family": "sans-serif", "font_size": 30,
        "lines": [("Table 2 bound in seconds of backlog", 155, 675, "left")]
    },
    {
        "id": "T2 Row 1",
        "box": (66, 700, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("0.0: hit 0.57, p50 0.22, p99 0.99, max/mean 1.22", 86, 732, "left")]
    },
    {
        "id": "T2 Row 2",
        "box": (66, 754, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("0.1: 0.89, 0.10, 0.52, 1.56", 86, 786, "left")]
    },
    {
        "id": "T2 Row 3",
        "box": (66, 808, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("0.5: 0.95, 0.10, 0.50, 2.13", 86, 840, "left")]
    },
    {
        "id": "T2 Row 4",
        "box": (66, 862, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("2.0: 0.98, 0.11, 1.68, 3.39", 86, 894, "left")]
    },
    {
        "id": "T2 Row 5",
        "box": (66, 916, 1468, 48),
        "font_family": "monospace", "font_size": 24,
        "lines": [("100 (cache-only): 0.98, 0.16, 4.39, 3.80", 86, 948, "left")]
    },
    {
        "id": "Takeaway Bar",
        "box": (50, 1010, 1500, 146),
        "font_family": "sans-serif", "font_size": 24,
        "lines": [
            ("cache-only wins hit rate and loses the tail because one replica carries 3.8 times the average load;", 800, 1046, "center"),
            ("least-loaded keeps load flat but wastes the cache; sweep the bound against p99, not hit rate;", 800, 1082, "center"),
            ("zero bound behaves like least-loaded, a huge bound like cache-only", 800, 1118, "center")
        ]
    }
]

print("=== PADDING VERIFICATION (>= 16px on all sides) ===")
all_pass = True
for c in cards:
    bx, by, bw, bh = c["box"]
    ff = c["font_family"]
    fs = c["font_size"]
    box_right = bx + bw
    box_bottom = by + bh
    
    # Check lines
    for text, lx, ly, align in c["lines"]:
        w = text_width(text, ff, fs)
        top, bottom = font_height_bounds(ly, fs)
        if align == "center":
            left = lx - w / 2
            right = lx + w / 2
        else:
            left = lx
            right = lx + w
            
        pad_left = left - bx
        pad_right = box_right - right
        pad_top = top - by
        pad_bottom = box_bottom - bottom
        
        ok_left = pad_left >= 16.0
        ok_right = pad_right >= 16.0
        ok_top = pad_top >= 16.0
        ok_bottom = pad_bottom >= 16.0
        
        ok = ok_left and ok_right and ok_top and ok_bottom
        if not ok:
            all_pass = False
            print(f"[FAIL] {c['id']}: '{text[:30]}...' pads: L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}")
        else:
            print(f"[PASS] {c['id']}: '{text[:30]}...' pads: L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}")
            
        if "icon" in c:
            ix, iy, iw, ih = c["icon"]
            icon_right = ix + iw
            assert left - icon_right >= 16.0, f"Icon clearance {left - icon_right} < 16px!"

print(f"\nALL PADDINGS >= 16px: {all_pass}")
