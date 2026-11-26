def run():
    factor_sans = 0.60
    factor_mono = 0.62
    
    checks = []
    
    # 1. Canvas Title
    checks.append((
        "Canvas Title",
        [
            ("awk group-by:", 48, 66, 800, "middle", False),
            ("an associative array counts as the lines pass", 48, 120, 800, "middle", False)
        ],
        0, 0, 1600, 140
    ))
    
    # 2. Left Input Table
    # Header
    checks.append((
        "Col 1 Header",
        [("column 1", 24, 250, 135, "middle", False)],
        60, 210, 150, 60
    ))
    checks.append((
        "Col 2 Header",
        [("column 2", 24, 250, 285, "middle", False)],
        210, 210, 150, 60
    ))
    
    # Rows
    names = ["alice", "bob", "alice", "alice", "bob"]
    for i, name in enumerate(names):
        ry = 280 + i * 76
        checks.append((
            f"Left Row {i+1} ({name})",
            [(name, 26, ry + 45, 135, "middle", True)],
            60, ry, 150, 64
        ))
        
    # 3. Middle Box
    checks.append((
        "Middle Header 'awk { c[$1]++ }'",
        [("awk { c[$1]++ }", 32, 192, 515, "left", True)],
        430, 140, 580, 70
    ))
    checks.append((
        "Lookup table c header",
        [("lookup table c", 26, 253, 720, "middle", False)],
        455, 210, 530, 60
    ))
    
    # Snapshots
    snap_configs = [
        (1, "after line 1", "alice = 1", 278),
        (2, "after line 3", "alice = 2, bob = 1", 408),
        (3, "after line 5", "alice = 3, bob = 2", 538),
    ]
    for num, step_lbl, val_lbl, sy in snap_configs:
        checks.append((
            f"Snapshot {num} Box",
            [
                (str(num), 26, sy + 62, 490, "middle", False),
                (step_lbl, 30, sy + 47, 535, "left", False),
                (val_lbl, 26, sy + 94, 550, "left", True)
            ],
            455, sy, 530, 118
        ))
        
    # 4. Right END Box
    checks.append((
        "Right END Box Title",
        [
            ("END { for (k in c)", 24, 180, 1305, "middle", True),
            ("print c[k], k }", 24, 214, 1305, "middle", True)
        ],
        1050, 140, 510, 90
    ))
    checks.append((
        "Right END runs once text",
        [("runs once after the last line", 24, 271, 1305, "middle", False)],
        1050, 230, 510, 60
    ))
    checks.append((
        "Right END Output Box",
        [
            ("output", 24, 350, 1100, "left", False),
            ("3 alice", 26, 340, 1330, "middle", True),
            ("2 bob", 26, 380, 1330, "middle", True)
        ],
        1075, 295, 460, 110
    ))
    
    # 5. Right Sort Box
    checks.append((
        "Right Sort Box Title",
        [("| sort -rn", 30, 472, 1150, "left", True)],
        1050, 425, 510, 70
    ))
    checks.append((
        "Right Sort Subtitle",
        [("ranked output", 24, 536, 1305, "middle", False)],
        1050, 495, 510, 60
    ))
    checks.append((
        "Right Sort Output Box",
        [
            ("3 alice", 26, 605, 1305, "middle", True),
            ("2 bob", 26, 645, 1305, "middle", True)
        ],
        1075, 560, 460, 110
    ))
    
    # 6. Comparison Panel
    checks.append((
        "Comp Left Title",
        [("uniq -c without sort", 28, 775, 475, "middle", True)],
        135, 730, 680, 64
    ))
    outputs_a = ["1 alice", "1 bob", "2 alice", "1 bob"]
    for i, out_txt in enumerate(outputs_a):
        ox = 155 + i * 162
        checks.append((
            f"Comp Left Card {i+1} ({out_txt})",
            [(out_txt, 26, 860, ox + 75, "middle", True)],
            ox, 800, 150, 110
        ))
        
    checks.append((
        "Comp Right Title",
        [("sort | uniq -c", 28, 775, 1190, "middle", True)],
        845, 730, 690, 64
    ))
    outputs_b = ["3 alice", "2 bob"]
    for i, out_txt in enumerate(outputs_b):
        ox = 895 + i * 300
        checks.append((
            f"Comp Right Card {i+1} ({out_txt})",
            [(out_txt, 30, 860, ox + 140, "middle", True)],
            ox, 800, 280, 110
        ))
        
    # 7. Takeaway Bar
    checks.append((
        "Bottom Takeaway Bar",
        [("An associative array is a lookup table keyed by text, so no sort | uniq -c is needed", 26, 1040, 800, "middle", False)],
        40, 990, 1520, 80
    ))
    
    all_passed = True
    failures = []
    for label, lines, bx, by, bw, bh in checks:
        for text, fs, base_y, ax, align, is_mono in lines:
            factor = factor_mono if is_mono else factor_sans
            lw = len(text) * fs * factor
            if align == "middle":
                tl = ax - lw / 2
                tr = ax + lw / 2
            elif align == "right":
                tl = ax - lw
                tr = ax
            else:
                tl = ax
                tr = ax + lw
            
            pl = tl - bx
            pr = (bx + bw) - tr
            pt = (base_y - fs) - by
            pb = (by + bh) - base_y
            
            if pl < 16 or pr < 16 or pt < 16 or pb < 16:
                all_passed = False
                failures.append(f"FAIL: {label} -> '{text}' ({fs}px): pl={pl:.1f}, pr={pr:.1f}, pt={pt:.1f}, pb={pb:.1f}")
            else:
                print(f"PASS: {label} -> '{text}' ({fs}px): pl={pl:.1f}, pr={pr:.1f}, pt={pt:.1f}, pb={pb:.1f}")
                
    if failures:
        print(f"\n{len(failures)} FAILURES:")
        for f in failures:
            print(f)
    else:
        print("\nALL 37 CHECKS PASSED STRICT >= 16PX PADDING!")

run()
