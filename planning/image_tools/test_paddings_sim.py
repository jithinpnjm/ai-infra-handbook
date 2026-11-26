cards = [
    # Card 1: T0
    {
        "id": "c1",
        "x": 60, "y": 120, "w": 900, "h": 210,
        "title": "T0",
        "title_fs": 32,
        "title_pos": (160, 170),
        "icon_pos": (85, 138),
        "body_fs": 24,
        "lines": [
            ("worker pod resolves trainer-0.trainer.ml before that", 160, 218),
            ("pod exists: NXDOMAIN, cached as a negative answer", 160, 254),
            ("(cache denial, SOA minimum 30 s)", 160, 290),
        ]
    },
    # Card 2: T0+few s
    {
        "id": "c2",
        "x": 60, "y": 370, "w": 900, "h": 150,
        "title": "T0+few s",
        "title_fs": 32,
        "title_pos": (160, 420),
        "icon_pos": (85, 388),
        "body_fs": 24,
        "lines": [
            ("trainer-0 pod starts and its record now exists", 160, 472),
        ]
    },
    # Card 3: Until T0+30 s (Orange highlight)
    {
        "id": "c3",
        "x": 60, "y": 560, "w": 900, "h": 190,
        "title": "Until T0+30 s",
        "title_fs": 32,
        "title_pos": (160, 610),
        "icon_pos": (85, 578),
        "body_fs": 24,
        "lines": [
            ("the worker keeps getting the cached NXDOMAIN:", 160, 664),
            ("sticky note saying no such person", 160, 702),
        ]
    },
    # Card 4: T0+30 s
    {
        "id": "c4",
        "x": 60, "y": 790, "w": 900, "h": 150,
        "title": "T0+30 s",
        "title_fs": 32,
        "title_pos": (160, 840),
        "icon_pos": (85, 808),
        "body_fs": 24,
        "lines": [
            ("cache entry expires, lookup succeeds, worker joins", 160, 892),
        ]
    },
    # Fix box
    {
        "id": "fix",
        "x": 1000, "y": 120, "w": 540, "h": 450,
        "icon_pos": (1035, 145),
        "body_fs": 24,
        "lines": [
            ("workers retry with backoff and", 1035, 232),
            ("bounded timeouts;", 1035, 266),
            ("applications avoid caching", 1035, 300),
            ("failures; headless Service with", 1035, 334),
            ("publishNotReadyAddresses true", 1035, 368),
            ("so peers resolve before ready;", 1035, 402),
            ("stagger startup", 1035, 436),
        ]
    },
    # Side box
    {
        "id": "side",
        "x": 1000, "y": 610, "w": 540, "h": 390,
        "icon_pos": (1035, 635),
        "body_fs": 24,
        "lines": [
            ("JVM caches successful lookups", 1035, 722),
            ("indefinitely with a security", 1035, 756),
            ("manager, 30 s without one;", 1035, 790),
            ("set TTL properties so", 1035, 824),
            ("clients drop old IPs", 1035, 858),
            ("after failover", 1035, 892),
        ]
    }
]

print("Checking paddings for all elements...")
all_ok = True
for c in cards:
    bx1 = c["x"]
    bx2 = c["x"] + c["w"]
    by1 = c["y"]
    by2 = c["y"] + c["h"]
    
    # Check title if present
    if "title" in c:
        t_str = c["title"]
        t_x, t_y = c["title_pos"]
        fs = c["title_fs"]
        w = len(t_str) * 0.6 * fs
        t_x2 = t_x + w
        t_y1 = t_y - fs
        t_y2 = t_y
        
        pad_l = t_x - bx1
        pad_r = bx2 - t_x2
        pad_t = t_y1 - by1
        pad_b = by2 - t_y2
        min_p = min(pad_l, pad_r, pad_t, pad_b)
        print(f"[{'OK' if min_p >= 16 else 'FAIL'}] Card {c['id']} Title '{t_str}': min_pad={min_p:.1f} (l={pad_l:.1f}, r={pad_r:.1f}, t={pad_t:.1f}, b={pad_b:.1f})")
        if min_p < 16: all_ok = False
        
    # Check body lines
    fs = c["body_fs"]
    for line_idx, (text, lx, ly) in enumerate(c["lines"]):
        w = len(text) * 0.6 * fs
        lx2 = lx + w
        ly1 = ly - fs
        ly2 = ly
        pad_l = lx - bx1
        pad_r = bx2 - lx2
        pad_t = ly1 - by1
        pad_b = by2 - ly2
        min_p = min(pad_l, pad_r, pad_t, pad_b)
        print(f"[{'OK' if min_p >= 16 else 'FAIL'}] Card {c['id']} line {line_idx}: '{text[:25]}...' min_pad={min_p:.1f} (l={pad_l:.1f}, r={pad_r:.1f}, t={pad_t:.1f}, b={pad_b:.1f})")
        if min_p < 16: all_ok = False

# Check icon paddings
for c in cards:
    ix, iy = c["icon_pos"]
    iw, ih = 56, 56
    bx1 = c["x"]
    bx2 = c["x"] + c["w"]
    by1 = c["y"]
    by2 = c["y"] + c["h"]
    pad_l = ix - bx1
    pad_r = bx2 - (ix + iw)
    pad_t = iy - by1
    pad_b = by2 - (iy + ih)
    min_p = min(pad_l, pad_r, pad_t, pad_b)
    print(f"[{'OK' if min_p >= 16 else 'FAIL'}] Card {c['id']} Icon: min_pad={min_p:.1f}")
    if min_p < 16: all_ok = False

# Check icon to text clearance
for c in cards:
    ix, iy = c["icon_pos"]
    iw, ih = 56, 56
    if "title" in c:
        tx, ty = c["title_pos"]
        gap = tx - (ix + iw)
        print(f"[{'OK' if gap >= 16 else 'FAIL'}] Card {c['id']} Icon-to-Title gap: {gap:.1f}px")
        if gap < 16: all_ok = False

assert all_ok
print("\nALL CARD PADDINGS AND CLEARANCES >= 16px PASSED!")
