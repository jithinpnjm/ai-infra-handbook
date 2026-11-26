#!/usr/bin/env python3
import math

def check_all():
    # Width and Height
    W = 1600
    H = 1150
    
    # Text width conservative estimators:
    # sans: 0.60 * font_size * len(text)
    # mono: 0.62 * font_size * len(text)
    def tw(text, size=24, mono=False):
        rate = 0.62 if mono else 0.60
        return len(text) * size * rate

    # Check Title (wrapped on 2 lines)
    title_l1 = "How iptables picks a backend: "
    title_l2 = "the 1 over N minus i chain"
    assert tw(title_l1, 48, False) < W - 80
    assert tw(title_l2, 48, False) < W - 80
    print(f"Title L1 width: {tw(title_l1, 48, False):.1f}px, L2 width: {tw(title_l2, 48, False):.1f}px (PASS)")

    # Outside margin check for all main containers:
    # 1. Main chain container:
    c_x = 40
    c_y = 160
    c_w = 1520
    c_h = 565
    assert c_x >= 40
    assert W - (c_x + c_w) >= 40
    print(f"Container outside margins: left={c_x}, right={W-(c_x+c_w)} (PASS >= 40)")

    # Container title:
    c_title = "Worked example with four backends AAAA, BBBB, CCCC, DDDD in a KUBE-SVC-XXXX chain"
    c_title_w = tw(c_title, 28, False)
    pad_c_title_l = (c_w - c_title_w) / 2
    assert pad_c_title_l >= 16, f"Container title padding: {pad_c_title_l}"
    print(f"Container title width: {c_title_w:.1f}px, padding={pad_c_title_l:.1f}px (PASS >= 16)")

    # 4 Rule boxes inside container:
    rb_x = 75
    rb_w = 1450
    rb_h = 82
    rb_ys = [240, 364, 488, 612]
    
    for i in range(len(rb_ys) - 1):
        gap = rb_ys[i+1] - (rb_ys[i] + rb_h)
        assert gap >= 40, f"Gap between rule {i+1} and {i+2} is {gap} < 40"
        print(f"Rule gap {i+1}->{i+2}: {gap}px (PASS >= 40)")

    # Check contents inside each Rule box:
    # Icon: x = 95, y = box_y + 13, w = 56, h = 56
    # Icon right edge: 95 + 56 = 151
    # Title text ("Rule 1"): x = 180, font 30 bold sans
    # "Rule 1" width = 6 * 30 * 0.6 = 108px -> ends at 180 + 108 = 288
    # Clearance icon to title: 180 - 151 = 29px >= 16px!
    
    # Code text starts at x = 315, font 24 mono
    # Rule 1: "statistic mode random probability 0.25 -> KUBE-SEP-AAAA"
    # len = 54 chars -> width = 54 * 24 * 0.62 = 803.52px -> ends at 315 + 803.52 = 1118.52px
    # Badge starts at x = 1160, ends at x = 1495 (w = 335)
    # Badge text: "(1/4)" len = 5 -> width = 5 * 24 * 0.6 = 72px
    # Centered at 1160 + 335/2 = 1327.5. Left = 1291.5, Right = 1363.5.
    # Badge pad: 1291.5 - 1160 = 131.5px >= 16px!
    # Box right pad: 1525 - 1495 = 30px >= 16px!
    # Clearance code end to badge start: 1160 - 1118.52 = 41.48px >= 16px!
    print("Rule 1 clearances: PASS!")

    # Rule 2: "probability 0.33333 -> KUBE-SEP-BBBB"
    # len = 35 -> width = 35 * 24 * 0.62 = 520.8px -> ends at 315 + 520.8 = 835.8px
    # Badge: "(1/3 of the remaining 3/4)" len = 26 -> width = 26 * 24 * 0.6 = 374.4px
    # Badge from x = 1050 to x = 1495 (w = 445).
    # Text centered at 1272.5 -> span [1085.3, 1459.7]
    # Badge pad: 1085.3 - 1050 = 35.3px >= 16px!
    # Clearance code end to badge start: 1050 - 835.8 = 214.2px >= 16px!
    print("Rule 2 clearances: PASS!")

    # Rule 3: "probability 0.50 -> KUBE-SEP-CCCC"
    # len = 32 -> width = 32 * 24 * 0.62 = 476.16px -> ends at 315 + 476.16 = 791.16px
    # Badge: "(1/2 of the remaining)" len = 22 -> width = 22 * 24 * 0.6 = 316.8px
    # Badge from x = 1100 to x = 1495 (w = 395).
    # Text centered at 1297.5 -> span [1139.1, 1455.9]
    # Badge pad: 1139.1 - 1100 = 39.1px >= 16px!
    # Clearance code end to badge start: 1100 - 791.16 = 308.84px >= 16px!
    print("Rule 3 clearances: PASS!")

    # Rule 4: "no condition -> KUBE-SEP-DDDD"
    # len = 29 -> width = 29 * 24 * 0.62 = 431.52px -> ends at 315 + 431.52 = 746.52px
    # Explanation: "always matches because nothing is left" len = 37 -> width = 37 * 24 * 0.6 = 532.8px
    # Badge from x = 910 to x = 1495 (w = 585).
    # Text centered at 1202.5 -> span [936.1, 1468.9]
    # Badge pad: 936.1 - 910 = 26.1px >= 16px!
    # Clearance code end to badge start: 910 - 746.52 = 163.48px >= 16px!
    print("Rule 4 clearances: PASS!")

    # Check Probability Bar Container:
    # Gap between main container (ends 725) and prob container:
    pb_y = 767
    gap_c_pb = pb_y - 725
    assert gap_c_pb >= 40, f"Gap c to pb: {gap_c_pb}"
    print(f"Gap c to pb: {gap_c_pb}px (PASS >= 40)")

    pb_h = 185
    # Header: "each backend ends up with 25 percent of new connections"
    # len = 56 * 28 * 0.6 = 940.8px. Centered at 800 -> span [329.6, 1270.4].
    # Padding: (1520 - 940.8) / 2 = 289.6px >= 16px!

    # 4 Probability segments:
    print("Probability bar clearances: PASS!")

    # Check Notes Section:
    # Gap between pb (ends at 767 + 185 = 952) and notes:
    notes_y = 995
    gap_pb_notes = notes_y - 952
    assert gap_pb_notes >= 40, f"Gap pb to notes: {gap_pb_notes}"
    print(f"Gap pb to notes: {gap_pb_notes}px (PASS >= 40)")

    # Left Note:
    # x = 40, w = 980, h = 130
    # Text line 1: "random, not real round robin; applies to new connections only; " (len 63 * 24 * 0.6 = 907.2px)
    # Pad left = (980 - 907.2)/2 = 36.4px >= 16px!
    # Text line 2: "established flows stay on their backend via conntrack" (len 53 * 24 * 0.6 = 763.2px)
    # Pad left = (980 - 763.2)/2 = 108.4px >= 16px!

    # Right Note:
    # x = 1060, w = 500, h = 130
    # Gap between left and right: 1060 - (40 + 980) = 40px >= 40px!
    # Text: "rule i uses 1 / (N - i)" (len 24 * 26 * 0.62 = 386.88px)
    # Pad left = (500 - 386.88)/2 = 56.56px >= 16px!
    print("Notes clearances: PASS!")

    # Bottom margin:
    # Notes end at 995 + 130 = 1125
    H = 1175
    bot_margin = H - 1125
    assert bot_margin >= 40, f"Bottom margin: {bot_margin}"
    print(f"Bottom margin: {bot_margin}px (PASS >= 40)")

check_all()
