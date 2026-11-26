#!/usr/bin/env python3

def check_all_conservative():
    # Format: (name, box_w, text_line, font_size, is_mono)
    tests = [
        # Step 1 inner card: w = 375
        ("Step 1 L1", 375, "1 perf record -F 99", 24, True),
        ("Step 1 L2", 375, "-a -g -- sleep 10", 24, True),
        
        # Step 2 inner card: w = 572
        ("Step 2 L1", 572, "2 perf script report", 24, True),
        ("Step 2 L2", 572, "flamegraph (perf 5.8 and newer)", 24, True),
        ("Step 2 L3", 572, "perf script,", 24, True),
        ("Step 2 L4", 572, "stackcollapse-perf.pl, flamegraph.pl", 24, True),
        
        # Step 3 inner card: w = 375
        ("Step 3 L1", 375, "3 Read the widest tower", 24, False),
        ("Step 3 L2", 375, "from the bottom upward", 24, False),
        
        # Callout 1: w = 390
        ("Callout 1 L1", 390, "Vertical axis:", 24, False),
        ("Callout 1 L2", 390, "stack depth, the top", 24, False),
        ("Callout 1 L3", 390, "box is what was on CPU", 24, False),
        
        # Callout 2: w = 390
        ("Callout 2 L1", 390, "Each box is", 24, False),
        ("Callout 2 L2", 390, "a function", 24, False),
        
        # Callout 3: w = 390
        ("Callout 3 L1", 390, "A wide box could", 24, False),
        ("Callout 3 L2", 390, "be slow or just", 24, False),
        ("Callout 3 L3", 390, "called often,", 24, False),
        ("Callout 3 L4", 390, "sampling does not", 24, False),
        ("Callout 3 L5", 390, "show call counts", 24, False),
        
        # Callout 4: w = 390
        ("Callout 4 L1", 390, "Left-to-right order", 24, False),
        ("Callout 4 L2", 390, "has no meaning, it is", 24, False),
        ("Callout 4 L3", 390, "alphabetical", 24, False),
        
        # Callout 5: w = 660
        ("Callout 5 L1", 660, "Horizontal axis: share of samples,", 24, False),
        ("Callout 5 L2", 660, "wider means more time", 24, False),
        
        # Bottom note: w = 1520 (with icon on left w=56 + gap=20 -> avail w = 1400)
        ("Bottom note L1", 1400, "One hot function may need a better algorithm.", 24, False),
        ("Bottom note L2", 1400, "Many small callers may need less work overall.", 24, False),
        
        # Takeaway bar: w = 1520
        ("Takeaway bar", 1520, "Reach for a profile only after a resource is proven short, and sample before you trace.", 26, False),
    ]
    
    all_ok = True
    print("=== CONSERVATIVE PADDING CHECK ===")
    for name, bw, text, fs, is_mono in tests:
        coeff = 0.62 if is_mono else 0.60
        est_w = len(text) * coeff * fs
        pad = (bw - est_w) / 2
        ok = pad >= 16.0
        if not ok:
            all_ok = False
        print(f"[{'PASS' if ok else 'FAIL'}] {name:15s} | len={len(text):2d} | est_w={est_w:5.1f}px | box_w={bw}px | pad={pad:5.1f}px")
        
    assert all_ok, "Some conservative padding checks failed!"
    print("\nALL CONSERVATIVE PADDINGS PASSED! (>= 16px)")

check_all_conservative()
