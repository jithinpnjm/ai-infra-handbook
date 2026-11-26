labels = {
    "title": "An SLO and alerting platform for 1,000 endpoints [my addition]",
    "y": "SLO file per endpoint",
    "gen": "Rule generator",
    "rec": "Recording rules",
    "br": "Burn-rate alerts",
    "rt": "Routing by owner",
    "m": "Metrics store"
}

fs_title = 48
cw_title = 0.6 * fs_title # 28.8

# Title splitting:
t_lines = ["An SLO and alerting platform", "for 1,000 endpoints [my addition]"]
for l in t_lines:
    w = len(l) * cw_title
    print(f"Title line: '{l}' len={len(l)} est_w={w:.1f} (max 1600-80={1520})")
    assert w <= 1520

fs_node = 30
cw_node = 0.6 * fs_node # 18.0
max_box_text_w = 260 - 32 # 228

splits = {
    "y": ["SLO file", "per endpoint"],
    "gen": ["Rule", "generator"],
    "rec": ["Recording", "rules"],
    "br": ["Burn-rate", "alerts"],
    "rt": ["Routing by", "owner"],
    "m": ["Metrics", "store"]
}

for k, lines in splits.items():
    orig = labels[k]
    reconstructed = " ".join(lines)
    assert reconstructed == orig, f"Mismatch: '{orig}' vs '{reconstructed}'"
    for l in lines:
        w = len(l) * cw_node
        print(f"Node [{k}] line: '{l}' len={len(l)} est_w={w:.1f} max={max_box_text_w}")
        assert w <= max_box_text_w, f"Line '{l}' exceeds {max_box_text_w} with {w}"

print("All text length tests PASSED!")
