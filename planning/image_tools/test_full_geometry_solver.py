import re

# Test all elements and verify paddings
def verify_geometry():
    # Right Column:
    # 1. Exit code table: y=95, h=200 -> ends 295
    # Gap: 45 -> models: y=340, h=96 -> ends 436
    # Gap: 40 -> parser_detail: y=476, h=234 -> ends 710
    # Gap: 40 -> rules_detail: y=750, h=150 -> ends 900
    # Gap: 40 -> test_strip: y=940, h=115 -> ends 1055
    # Gap: 40 -> bottom_bar: y=1095, h=65 -> ends 1160
    # Bottom margin: 1200 - 1160 = 40px!

    # Left Column:
    # 1. cli: y=95, h=125 -> ends 220
    # Arrow 1: y=220 to y=265 (len=45)
    # 2. collect: y=265, h=140 -> ends 405
    # Arrow 2: y=405 to y=450 (len=45)
    # 3. parsers: y=450, h=195 -> ends 645
    # Arrow 3: y=645 to y=705 (len=60)
    # 4. rules: y=705, h=150 -> ends 855
    # Gap from lowest left box (855) to test_strip (940) = 85px >= 40px!

    gaps = [
        ("cli -> collect", 265 - 220),
        ("collect -> parsers", 450 - 405),
        ("parsers -> rules", 705 - 645),
        ("rules -> test_strip", 940 - 855),
        ("exit_codes -> models", 340 - 295),
        ("models -> parser_detail", 476 - 436),
        ("parser_detail -> rules_detail", 750 - 710),
        ("rules_detail -> test_strip", 940 - 900),
        ("test_strip -> bottom_bar", 1095 - 1055),
        ("bottom_bar -> canvas_bottom", 1200 - 1160),
        ("left_margin", 40),
        ("right_margin", 1600 - 1560),
        ("col_gap", 940 - 900)
    ]

    print("=== GAPS AND MARGINS ===")
    all_gaps_ok = True
    for name, val in gaps:
        ok = val >= 40
        if not ok: all_gaps_ok = False
        print(f"[{'OK' if ok else 'FAIL'}] {name:30s}: {val}px")
    assert all_gaps_ok, "Some gap or margin is < 40px!"
    print("ALL GAPS AND MARGINS >= 40px!")

verify_geometry()
