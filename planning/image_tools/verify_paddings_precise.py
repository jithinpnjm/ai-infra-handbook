#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse('candidate_file_sd.svg')
root = tree.getroot()

checks = [
    # (name, text, font_family, font_size, box_x, box_y, box_w, box_h, text_anchor, text_x, y, icon_box)
    # icon_box is optional (ix, iy, iw, ih) to ensure no overlap!
    ("Title line 1", "Two rendered outputs: Prometheus file_sd targets", "sans", 48, 0, 0, 1600, 145, "middle", 800, 50, None),
    ("Title line 2", "and YAML from data", "sans", 48, 0, 0, 1600, 145, "middle", 800, 104, None),
    ("P1 Header Title", "Prometheus file_sd targets", "sans", 30, 40, 145, 740, 80, "start", 142, 200, (68, 162, 56, 56)),
    ("P1 Step 1", "groups[gpu]", "mono", 24, 75, 236, 670, 54, "middle", 410, 271, None),
    ("P1 Step 2", "map(extract, hostvars, ansible_host)", "mono", 24, 75, 314, 670, 54, "middle", 410, 349, None),
    ("P1 Step 3 line 1", "map(regex_replace, $, :9400)", "mono", 24, 75, 392, 670, 124, "middle", 410, 428, None),
    ("P1 Step 3 line 2", "appends port 9400, where the DCGM exporter", "sans", 24, 75, 392, 670, 124, "middle", 410, 460, None),
    ("P1 Step 3 line 3", "listens for GPU metrics", "sans", 24, 75, 392, 670, 124, "middle", 410, 492, None),
    ("P1 Step 4", "list", "mono", 24, 75, 540, 670, 54, "middle", 410, 575, None),
    ("P1 Step 5 targets", "targets", "mono", 24, 95, 626, 630, 50, "middle", 410, 659, None),
    ("P1 Step 5 labels L1", "labels: job dcgm,", "mono", 24, 95, 682, 630, 80, "middle", 410, 716, None),
    ("P1 Step 5 labels L2", "cluster {{ cluster_name }}", "mono", 24, 95, 682, 630, 80, "middle", 410, 746, None),
    ("P1 Step 6", "to_nice_json", "mono", 24, 75, 794, 670, 54, "middle", 410, 829, None),
    ("P1 Note L1", "file_sd means file-based service", "sans", 24, 75, 876, 670, 190, "middle", 410, 946, (392, 888, 36, 36)),
    ("P1 Note L2", "discovery: Prometheus re-reads the file", "sans", 24, 75, 876, 670, 190, "middle", 410, 978, (392, 888, 36, 36)),
    ("P1 Note L3", "on its own schedule, so a new node added", "sans", 24, 75, 876, 670, 190, "middle", 410, 1010, (392, 888, 36, 36)),
    ("P1 Note L4", "to the file is scraped without a restart", "sans", 24, 75, 876, 670, 190, "middle", 410, 1042, (392, 888, 36, 36)),
    ("P2 Header Title", "YAML from data", "sans", 30, 820, 145, 740, 80, "start", 922, 200, (848, 162, 56, 56)),
    ("P2 Card 1 L1", "{{ k8s_values | to_nice_yaml(indent=2)", "mono", 26, 855, 240, 670, 150, "middle", 1190, 322, (1172, 252, 36, 36)),
    ("P2 Card 1 L2", "| indent(4) }}", "mono", 26, 855, 240, 670, 150, "middle", 1190, 364, (1172, 252, 36, 36)),
    ("P2 Card 2 L1", "hand-indented YAML is fragile, one space", "sans", 24, 855, 415, 670, 350, "middle", 1190, 522, (1162, 430, 56, 56)),
    ("P2 Card 2 L2", "in the wrong place changes the meaning", "sans", 24, 855, 415, 670, 350, "middle", 1190, 556, (1162, 430, 56, 56)),
    ("P2 Card 2 L3", "of the whole file; to_nice_yaml builds", "sans", 24, 855, 415, 670, 350, "middle", 1190, 590, (1162, 430, 56, 56)),
    ("P2 Card 2 L4", "the structure correctly every time and", "sans", 24, 855, 415, 670, 350, "middle", 1190, 624, (1162, 430, 56, 56)),
    ("P2 Card 2 L5", "indent(4) moves the block to the right", "sans", 24, 855, 415, 670, 350, "middle", 1190, 658, (1162, 430, 56, 56)),
    ("P2 Card 2 L6", "depth inside the surrounding template", "sans", 24, 855, 415, 670, 350, "middle", 1190, 692, (1162, 430, 56, 56)),
    ("P2 Card 3 L1", "then validate with yamllint or", "sans", 24, 855, 795, 670, 271, "middle", 1190, 920, (1162, 815, 56, 56)),
    ("P2 Card 3 L2", "kubeconform so a mistake is caught", "sans", 24, 855, 795, 670, 271, "middle", 1190, 956, (1162, 815, 56, 56)),
    ("P2 Card 3 L3", "before it reaches a cluster", "sans", 24, 855, 795, 670, 271, "middle", 1190, 992, (1162, 815, 56, 56)),
    ("Bottom bar", "Let filters build the structure, validate the result", "sans", 28, 40, 1115, 1520, 60, "middle", 800, 1154, None),
]

all_pass = True
for name, text, font, fs, bx, by, bw, bh, anchor, tx, ty, icon in checks:
    char_w = 0.62 * fs if font == "mono" else 0.60 * fs
    est_w = len(text) * char_w
    if anchor == "middle":
        x_left = tx - est_w / 2
        x_right = tx + est_w / 2
    else:
        x_left = tx
        x_right = tx + est_w
    
    pad_left = x_left - bx
    pad_right = (bx + bw) - x_right
    pad_top = (ty - fs*0.7) - by
    pad_bot = (by + bh) - ty

    # Check icon collision
    icon_collision = False
    if icon:
        ix, iy, iw, ih = icon
        # bounding box of text line: [x_left, ty - fs*0.8, x_right, ty + fs*0.2]
        # icon box: [ix, iy, ix + iw, iy + ih]
        t_top = ty - fs * 0.8
        t_bot = ty + fs * 0.2
        overlap_x = max(0, min(x_right, ix + iw) - max(x_left, ix))
        overlap_y = max(0, min(t_bot, iy + ih) - max(t_top, iy))
        if overlap_x > 0 and overlap_y > 0:
            icon_collision = True
    
    ok = (pad_left >= 16 and pad_right >= 16 and pad_top >= 15 and pad_bot >= 15 and not icon_collision)
    if not ok:
        all_pass = False
        print(f"[FAIL] {name}: pad_l={pad_left:.1f}, pad_r={pad_right:.1f}, pad_t={pad_top:.1f}, pad_b={pad_bot:.1f}, icon_collision={icon_collision}")
    else:
        print(f"[PASS] {name:20s}: pad_l={pad_left:5.1f}, pad_r={pad_right:5.1f}, pad_t={pad_top:4.1f}, pad_b={pad_bot:4.1f}")

assert all_pass, "Some padding checks failed!"
print("\nALL 30 CHECKS (PADDINGS + ZERO ICON OVERLAP) PASSED PERFECTLY!")
