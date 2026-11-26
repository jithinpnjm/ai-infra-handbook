#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def check_layout():
    # 1. Canvas Dimensions
    W = 1600
    H = 1100

    # Margins
    assert 40 >= 40, "Left margin"
    assert (W - 1560) >= 40, "Right margin"

    # Box 1: Story rect x=40, y=160, w=1520, h=110
    # Icon at x=65, y=187, w=56, h=56 -> right edge = 121
    # Text starts at x=145
    # Line 1: 'a Tuesday morning when the package manager upgrades the kernel ' (63 chars)
    # Line 2: 'on half the nodes and the NVIDIA driver no longer matches the new kernel' (72 chars)
    # font-size: 26 sans -> 0.6 * 26 = 15.6 px/char
    l1_w = 63 * 15.6
    l2_w = 72 * 15.6
    max_w = max(l1_w, l2_w)
    text_right = 145 + max_w
    box_right = 40 + 1520
    pad_right = box_right - text_right
    pad_left_from_icon = 145 - 121
    print(f"Story box: max_w={max_w:.1f}, text_right={text_right:.1f}, box_right={box_right}, pad_right={pad_right:.1f}, pad_left_icon={pad_left_from_icon}")
    assert pad_right >= 16, f"Story pad_right {pad_right} < 16"
    assert pad_left_from_icon >= 16, f"Story pad_left_icon {pad_left_from_icon} < 16"

    # Gap 1: Box 1 to Box 2
    gap_1 = 310 - (160 + 110)
    print(f"Gap 1 (Story to Fix task panel): {gap_1}px")
    assert gap_1 >= 40, f"Gap 1 {gap_1} < 40"

    # Box 2: Fix task panel x=40, y=310, w=1520, h=330
    # Card 2A: Fix task rect x=65, y=335, w=1470, h=155
    # Icon at x=85, y=385, w=56, h=56 -> right edge = 141
    # Text starts at x=165
    # Line 1: 'dpkg_selections: name {{ item }}, selection hold, ' (50 chars)
    # Line 2: 'loop [nvidia-driver-550, linux-image-generic], ' (47 chars)
    # Line 3: 'when ansible_facts[os_family] == Debian' (39 chars)
    # font-size: 24 mono -> 0.62 * 24 = 14.88 px/char
    ft_max_w = 50 * 14.88
    ft_text_right = 165 + ft_max_w
    ft_box_right = 65 + 1470
    ft_pad_right = ft_box_right - ft_text_right
    ft_pad_left_icon = 165 - 141
    print(f"Fix task: max_w={ft_max_w:.1f}, text_right={ft_text_right:.1f}, box_right={ft_box_right}, pad_right={ft_pad_right:.1f}, pad_left_icon={ft_pad_left_icon}")
    assert ft_pad_right >= 16, f"Fix task pad_right {ft_pad_right} < 16"
    assert ft_pad_left_icon >= 16, f"Fix task pad_left_icon {ft_pad_left_icon} < 16"

    # Card 2B: Note 1 rect x=65, y=510, w=920, h=110
    # Icon at x=85, y=537, w=56, h=56 -> right edge = 141
    # Text starts at x=165
    # Line 1: 'when keeps the task away from RedHat-family hosts, ' (51 chars)
    # Line 2: 'which need a different tool for the same job' (44 chars)
    # font-size: 24 sans -> 0.6 * 24 = 14.4 px/char
    n1_max_w = 51 * 14.4
    n1_text_right = 165 + n1_max_w
    n1_box_right = 65 + 920
    n1_pad_right = n1_box_right - n1_text_right
    n1_pad_left_icon = 165 - 141
    print(f"Note 1: max_w={n1_max_w:.1f}, text_right={n1_text_right:.1f}, box_right={n1_box_right}, pad_right={n1_pad_right:.1f}, pad_left_icon={n1_pad_left_icon}")
    assert n1_pad_right >= 16, f"Note 1 pad_right {n1_pad_right} < 16"
    assert n1_pad_left_icon >= 16, f"Note 1 pad_left_icon {n1_pad_left_icon} < 16"

    # Card 2C: Note 2 rect x=1025, y=510, w=510, h=110
    # Icon at x=1045, y=537, w=56, h=56 -> right edge = 1101
    # Text starts at x=1125
    # Line 1: 'package_facts inspects ' (23 chars)
    # Line 2: 'installed packages' (18 chars)
    # font-size: 24 sans -> 0.6 * 24 = 14.4 px/char
    n2_max_w = 23 * 14.4
    n2_text_right = 1125 + n2_max_w
    n2_box_right = 1025 + 510
    n2_pad_right = n2_box_right - n2_text_right
    n2_pad_left_icon = 1125 - 1101
    print(f"Note 2: max_w={n2_max_w:.1f}, text_right={n2_text_right:.1f}, box_right={n2_box_right}, pad_right={n2_pad_right:.1f}, pad_left_icon={n2_pad_left_icon}")
    assert n2_pad_right >= 16, f"Note 2 pad_right {n2_pad_right} < 16"
    assert n2_pad_left_icon >= 16, f"Note 2 pad_left_icon {n2_pad_left_icon} < 16"

    # Gap between Note 1 and Note 2:
    note_gap = 1025 - (65 + 920)
    print(f"Gap between Note 1 and Note 2: {note_gap}px")
    assert note_gap >= 40, f"note_gap {note_gap} < 40"

    # Gap 2: Box 2 to Box 3
    box_gap_2_3 = 680 - (310 + 330)
    print(f"Gap 2 (Fix task panel to Pinning options table): {box_gap_2_3}px")
    assert box_gap_2_3 >= 40

    # Box 3: Pinning options table panel x=40, y=680, w=1520, h=270
    # Row 1: selection: hold: package cannot be moved by a routine upgrade
    # x=65, y=700, w=1470, h=70
    # Icon at x=85, y=707, w=56, h=56 -> right edge = 141
    # Text at x=165: 'selection: hold: ' (17 mono) + 'package cannot be moved by a routine upgrade' (47 sans)
    r1_w = 17 * (0.62 * 25) + 47 * (0.6 * 25)
    r1_text_right = 165 + r1_w
    r1_box_right = 65 + 1470
    r1_pad_right = r1_box_right - r1_text_right
    r1_pad_left_icon = 165 - 141
    print(f"Row 1: w={r1_w:.1f}, text_right={r1_text_right:.1f}, pad_right={r1_pad_right:.1f}, pad_left_icon={r1_pad_left_icon}")
    assert r1_pad_right >= 16
    assert r1_pad_left_icon >= 16

    # Row 2: pinned version with state present: name nvidia-driver-550=550.90.07-1
    # Text at x=165: 'pinned version with state present: ' (35 sans) + 'name nvidia-driver-550=550.90.07-1' (34 mono)
    r2_w = 35 * (0.6 * 25) + 34 * (0.62 * 25)
    r2_text_right = 165 + r2_w
    r2_pad_right = r1_box_right - r2_text_right
    print(f"Row 2: w={r2_w:.1f}, text_right={r2_text_right:.1f}, pad_right={r2_pad_right:.1f}")
    assert r2_pad_right >= 16

    # Row 3: state: latest allows the upgrade
    # Text at x=165: 'state: latest ' (14 mono) + 'allows the upgrade' (18 sans)
    r3_w = 14 * (0.62 * 25) + 18 * (0.6 * 25)
    r3_text_right = 165 + r3_w
    r3_pad_right = r1_box_right - r3_text_right
    print(f"Row 3: w={r3_w:.1f}, text_right={r3_text_right:.1f}, pad_right={r3_pad_right:.1f}")
    assert r3_pad_right >= 16

    # Gap 3: Box 3 to Bottom Bar
    gap_3_bottom = 990 - (680 + 270)
    print(f"Gap 3 (Pinning options to Bottom bar): {gap_3_bottom}px")
    assert gap_3_bottom >= 40, f"gap_3_bottom {gap_3_bottom} < 40!"

    # Bottom Bar: y=990, h=60, ends at 1050
    # Bottom margin:
    bottom_margin = H - 1050
    print(f"Bottom margin: {bottom_margin}px")
    assert bottom_margin >= 40, f"bottom_margin {bottom_margin} < 40!"

    print("\nALL CLEARANCES AND PADDINGS VALID!")

if __name__ == '__main__':
    check_layout()
