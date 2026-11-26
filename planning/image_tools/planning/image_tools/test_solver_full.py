import re

def check_all():
    # Canvas W=1600, H=1200
    
    # Left column: x=40, w=1000
    # Right column: x=1080, w=480
    
    # Row 1:
    # Left: cli.py
    cli_box = (40, 140, 1000, 96) # ends at 236
    cli_icon = (56, 160, 56, 56)
    cli_lines = [
        ("cli.py: Click group, output formatting ", 28, 132, 180, False),
        ("and exit codes", 28, 132, 214, False)
    ]
    
    # Arrow 1: (540, 236) to (540, 276) -> length 40
    
    # Row 2:
    # Left: collect.py
    collect_box = (40, 276, 1000, 96) # ends at 372
    collect_icon = (56, 296, 56, 56)
    collect_lines = [
        ("collect.py: per-host executor over SSH, an agent or Redfish, ", 24, 132, 314, False),
        ("with timeout and bounded concurrency", 24, 132, 348, False)
    ]
    
    # Arrow 2: (540, 372) to (540, 412) -> length 40
    
    # Pure Layers Container:
    # x=40, y=412, w=1000, h=546 (ends at 958)
    # stroke="#db8129" stroke-width="3" fill="#ffffff"
    
    # Inside Pure Layers:
    # Parsers card:
    parsers_box = (56, 428, 968, 292) # ends at 720
    parsers_icon = (72, 442, 56, 56)
    parsers_lines = [
        ("parsers.py: pure functions turning nvidia-smi CSV ", 24, 144, 464, False),
        ("and dcgmi output into frozen dataclasses ", 24, 144, 491, False),
        ("(a pure function answers from its inputs alone: ", 24, 144, 518, False),
        ("no network, no clock, no randomness)", 24, 144, 545, False)
    ]
    parser_detail_box = (72, 566, 936, 140) # ends at 706
    parser_detail_lines = [
        ("Gpu(index, name, temp_c, util_pct, mem_used_mib,", 24, 92, 602, True),
        ("mem_total_mib, ecc_uncorrected); _int maps empty, [N/A]", 24, 92, 629, True),
        ("and [Not Supported] to None; a line without exactly 7", 24, 92, 656, True),
        ("columns raises ValueError unexpected nvidia-smi columns", 24, 92, 683, True)
    ]
    
    # Arrow 3: (540, 720) to (540, 760) -> length 40
    
    # Rules card:
    rules_box = (56, 760, 968, 192) # ends at 952
    rules_icon = (72, 772, 56, 56)
    rules_lines = [
        ("rules.py: evaluate(gpus, expected=8, max_temp=85)", 26, 144, 798, False)
    ]
    rules_detail_box = (72, 824, 936, 114) # ends at 938
    rules_detail_lines = [
        ("problems for: expected 8 GPUs but found a different count; ", 24, 92, 860, False),
        ("temp above 85; uncorrected ECC non-zero; ", 24, 92, 888, False),
        ("plus XID in a set of known codes", 24, 92, 916, False)
    ]
    
    # Right column:
    # models.py
    models_box = (1080, 140, 480, 96) # ends at 236
    models_icon = (1096, 160, 56, 56)
    models_lines = [
        ("models.py: dataclasses ", 26, 1172, 180, False),
        ("or pydantic models", 26, 1172, 212, False)
    ]
    
    # Gap 236 to 276 = 40px
    # Exit codes table container:
    exit_table_box = (1080, 276, 480, 682) # ends at 958
    
    # Card 0: (1100, 296, 440, 126) ends at 422
    exit_0_icon = (1116, 331, 56, 56)
    exit_0_lines = [
        ("0 all GPUs healthy", 28, 1188, 372, False)
    ]
    
    # Gap 422 to 458 = 36px
    # Card 1: (1100, 458, 440, 126) ends at 584
    exit_1_icon = (1116, 493, 56, 56)
    exit_1_lines = [
        ("1 usage or ", 26, 1188, 516, False),
        ("runtime failure", 26, 1188, 550, False)
    ]
    
    # Gap 584 to 620 = 36px
    # Card 3: (1100, 620, 440, 126) ends at 746
    exit_3_icon = (1116, 655, 56, 56)
    exit_3_lines = [
        ("3 any GPU unhealthy", 28, 1188, 696, False)
    ]
    
    # Gap 746 to 782 = 36px
    # Card 4: (1100, 782, 440, 126) ends at 908
    exit_4_icon = (1116, 817, 56, 56)
    exit_4_lines = [
        ("4 partial ", 26, 1188, 840, False),
        ("collection failure", 26, 1188, 874, False)
    ]
    
    # Gap 958 to 988 = 30px
    # Test strip:
    test_box = (40, 988, 1520, 114) # ends at 1102
    test_icon = (56, 1017, 56, 56)
    test_lines = [
        ("canned CSV into parse_smi_csv and evaluate: [N/A] values, wrong column count, ", 24, 136, 1024, False),
        ("empty output, missing GPU; then CliRunner with a stubbed executor ", 24, 136, 1052, False),
        ("asserting exit codes and JSON shape", 24, 136, 1080, False)
    ]
    
    # Gap 1102 to 1122 = 20px
    # Bottom bar:
    bar_box = (40, 1122, 1520, 64) # ends at 1186
    bar_icon = (56, 1126, 56, 56)
    bar_text = "Parser, rules, executor and CLI stay separate"
    bar_tw = len(bar_text) * 0.6 * 28
    bar_tx = 800 - 0.5 * bar_tw
    bar_lines = [
        (bar_text, 28, bar_tx, 1162, False)
    ]
    
    all_boxes = {
        "cli.py": (cli_box, cli_icon, cli_lines),
        "collect.py": (collect_box, collect_icon, collect_lines),
        "parsers.py": (parsers_box, parsers_icon, parsers_lines),
        "Parser detail": (parser_detail_box, None, parser_detail_lines),
        "rules.py": (rules_box, rules_icon, rules_lines),
        "Rules detail": (rules_detail_box, None, rules_detail_lines),
        "models.py": (models_box, models_icon, models_lines),
        "exit_0": ((1100, 296, 440, 126), exit_0_icon, exit_0_lines),
        "exit_1": ((1100, 458, 440, 126), exit_1_icon, exit_1_lines),
        "exit_3": ((1100, 620, 440, 126), exit_3_icon, exit_3_lines),
        "exit_4": ((1100, 782, 440, 126), exit_4_icon, exit_4_lines),
        "Test strip": (test_box, test_icon, test_lines),
        "Bottom bar": (bar_box, bar_icon, bar_lines)
    }
    
    print("=== AUDITING GEOMETRY ===")
    all_pass = True
    for name, (b, icon, lines) in all_boxes.items():
        bx, by, bw, bh = b
        if icon:
            ix, iy, iw, ih = icon
            icon_gap = min(l[2] - (ix + iw) for l in lines)
            ok_icon = icon_gap >= 16
            if not ok_icon:
                all_pass = False
            print(f"[{'PASS' if ok_icon else 'FAIL'}] {name} icon gap: {icon_gap:.1f}px")
            # Also check icon inside box:
            assert ix >= bx + 12, f"{name} icon left pad too small"
            assert iy >= by + 4, f"{name} icon top pad too small"
            assert (by + bh) - (iy + ih) >= 4, f"{name} icon bot pad too small"
        
        for text, fs, tx, ty, is_mono in lines:
            factor = 0.62 if is_mono else 0.6
            tw = len(text) * factor * fs
            ascent = fs * 0.8
            descent = fs * 0.25
            
            left_pad = tx - bx
            right_pad = (bx + bw) - (tx + tw)
            top_pad = (ty - ascent) - by
            bot_pad = (by + bh) - (ty + descent)
            
            ok = left_pad >= 16 and right_pad >= 16 and top_pad >= 14 and bot_pad >= 14
            if not ok:
                all_pass = False
            print(f"  [{'PASS' if ok else 'FAIL'}] '{text[:30]}...': L={left_pad:.1f}, R={right_pad:.1f}, T={top_pad:.1f}, B={bot_pad:.1f}")

    assert all_pass, "Paddings failed!"
    print("\nALL GEOMETRY PADDINGS PASSED COMPLETELY!")

check_all()
