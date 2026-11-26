# Test bounding boxes and paddings
# Box 1: x in [40, 390], w=350, center=215
# Box 2: x in [430, 780], w=350, center=605
# Box 3: x in [820, 1170], w=350, center=995
# Box 4: x in [1210, 1560], w=350, center=1385

lines = [
    # (box_idx, text, font_type, font_size)
    (1, "1. Utility /", "sans", 30),
    (1, "Generator + UPS", "sans", 30),
    (1, "apcupsd (:3551) +", "mono", 24),
    (1, "Staged haltall", "mono", 24),
    (2, "2. 3-Phase", "sans", 30),
    (2, "Rack PDUs (N=2)", "sans", 30),
    (2, "sqrt(3) * V * I *", "mono", 24),
    (2, "0.80 * 0.95", "mono", 24),
    (3, "3. GPU Server", "sans", 30),
    (3, "(DGX B200", "sans", 30),
    (3, "14.3 kW)", "sans", 30),
    (3, "6 PSUs", "sans", 24),
    (3, "(5-of-6", "sans", 24),
    (3, "N+1 Required)", "sans", 24),
    (4, "4. Heat", "sans", 30),
    (4, "Rejection", "sans", 30),
    (4, "(100% of Watts)", "sans", 30),
    (4, "Air (150 CFM/kW) or", "sans", 24),
    (4, "Cold-Plate CDU", "sans", 24),
]

box_width = 350
min_padding = 16

for b_idx, text, ftype, fsize in lines:
    factor = 0.6 if ftype == "sans" else 0.62
    width = len(text) * fsize * factor
    padding = (box_width - width) / 2
    print(f"Box {b_idx} | [{ftype} {fsize}px] '{text}': est_w={width:.1f}px, padding={padding:.1f}px")
    assert padding >= min_padding, f"Padding {padding} < {min_padding} for '{text}'"

print("ALL PADDINGS EXCEED 16px REQUIREMENT!")
