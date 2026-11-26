# Let's test the cascade:
# models: y=336, h=94 -> ends 430
# gap = 40 -> parser_detail: y=470, h=230 -> ends 700
# gap = 40 -> rules_detail: y=740, h=150 -> ends 890
# gap = 45 -> test_strip: y=935, h=120 -> ends 1055
# gap = 40 -> bottom_bar: y=1095, h=65 -> ends 1160
# margin_bottom: 1200 - 1160 = 40px!

# Left column:
# cli: y=95, h=125 -> ends 220
# arrow 1: y=220 to y=265 (len=45)
# collect: y=265, h=140 -> ends 405
# arrow 2: y=405 to y=450 (len=45)
# parsers: y=450, h=195 -> ends 645
# arrow 3: y=645 to y=705 (len=60)
# rules: y=705, h=150 -> ends 855
# gap to test_strip: 935 - 855 = 80px >= 40px!

# Right column top:
# exit_codes: y=95, h=200 -> ends 295
# gap to models: 336 - 295 = 41px >= 40px!

gaps = [
    ("exit_codes -> models", 336 - 295),
    ("models -> parser_detail", 470 - 430),
    ("parser_detail -> rules_detail", 740 - 700),
    ("rules_detail -> test_strip", 935 - 890),
    ("test_strip -> bottom_bar", 1095 - 1055),
    ("bottom_bar -> canvas_bottom", 1200 - 1160),
    ("cli -> collect", 265 - 220),
    ("collect -> parsers", 450 - 405),
    ("parsers -> rules", 705 - 645),
    ("rules -> test_strip", 935 - 855)
]

for name, g in gaps:
    assert g >= 40, f"FAILED: {name} gap {g} < 40"
    print(f"[OK] {name:30s}: {g}px")

print("\nALL GAPS SATISFIED!")
