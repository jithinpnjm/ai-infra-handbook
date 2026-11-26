# Test complete layout with strict constraints:
# 1. Canvas: 1600 x 1200
# 2. Outside margin: >= 40px
# 3. Inter-box gap: >= 40px
# 4. Box padding: >= 16px (left, right, top, bottom for every text line)
# 5. Font size: >= 24px everywhere

def test_box_padding(name, bx, by, bw, bh, lines):
    all_ok = True
    print(f"\nChecking {name} [box: ({bx}, {by}, {bw}, {bh})]:")
    for text, fs, is_mono, tx, ty, anchor in lines:
        char_w = 0.62 * fs if is_mono else 0.6 * fs
        tw = len(text) * char_w
        if anchor == "middle":
            x_min = tx - tw / 2
            x_max = tx + tw / 2
        else:
            x_min = tx
            x_max = tx + tw
        y_min = ty - fs * 0.85
        y_max = ty + fs * 0.25
        
        pad_l = x_min - bx
        pad_r = (bx + bw) - x_max
        pad_t = y_min - by
        pad_b = (by + bh) - y_max
        min_p = min(pad_l, pad_r, pad_t, pad_b)
        ok = min_p >= 16.0
        if not ok:
            all_ok = False
        print(f"  [{'PASS' if ok else 'FAIL'}] '{text[:32]}...' min={min_p:4.1f}px (L={pad_l:4.1f}, R={pad_r:4.1f}, T={pad_t:4.1f}, B={pad_b:4.1f})")
    return all_ok

# Title
t_ok = test_box_padding("Title", 40, 40, 1520, 110, [
    ("Is this partition aligned?", 48, False, 800, 85, "middle"),
    ("Divide the start sector by 8", 48, False, 800, 137, "middle")
])

# Strip: y=185, h=80
# Gap from title bottom (137 + 12 = 149) to strip (185) is 36px. Wait, if title box is 40..145, gap to 185 is 40px!

# Row A: y=305, h=230 (ends at 535)
# Gap from Strip (185+80=265) to Row A (305) is 40px!
row_a_ok = test_box_padding("Row A Container", 40, 305, 1520, 230, [
    ("Start sector 2048 (1 MiB)", 30, False, 140, 355, "left")
])
row_a_verdict = test_box_padding("Row A Verdict", 1340, 320, 200, 68, [
    ("aligned", 30, False, 1440, 362, "middle")
])
row_a_math = test_box_padding("Row A Math", 65, 388, 870, 62, [
    ("2048 / 8 = 256, a whole number, remainder 0", 25, True, 85, 426, "left")
])
row_a_bound = test_box_padding("Row A Boundary", 65, 458, 870, 62, [
    ("the partition boundary line sits exactly on a page edge", 24, False, 85, 496, "left")
])

# Row B: y=575, h=285 (ends at 860)
# Gap from Row A (535) to Row B (575) is 40px!
row_b_ok = test_box_padding("Row B Container", 40, 575, 1520, 285, [
    ("cat /sys/block/sdf/sdf2/start prints 1953126", 28, True, 140, 622, "left")
])
row_b_verdict = test_box_padding("Row B Verdict", 1290, 588, 250, 68, [
    ("NOT aligned", 30, False, 1415, 630, "middle")
])
row_b_math = test_box_padding("Row B Math", 65, 652, 1010, 60, [
    ("1953126 / 8 = 244140.75, remainder 6", 25, True, 85, 690, "left")
])
row_b_bound = test_box_padding("Row B Boundary", 65, 720, 1010, 60, [
    ("the partition boundary line falls inside a page, six sectors in", 24, False, 85, 758, "left")
])
row_b_strad = test_box_padding("Row B Straddle", 65, 788, 1010, 60, [
    ("a single 4 KiB read straddles two physical pages", 24, False, 85, 826, "left")
])

# Note Boxes: y=900, h=145 (ends at 1045)
# Gap from Row B (860) to Note Boxes (900) is 40px!
left_note = test_box_padding("Left Note", 40, 900, 730, 145, [
    ("Why 8: eight 512-byte sectors", 24, False, 140, 955, "left"),
    ("make one 4,096-byte page", 24, False, 140, 995, "left")
])
right_note = test_box_padding("Right Note", 800, 900, 760, 145, [
    ("Check with a tool:", 24, True, 900, 942, "left"),
    ("parted /dev/sdb align-check", 24, True, 900, 976, "left"),
    ("optimal 1 prints 1 aligned", 24, True, 900, 1010, "left")
])

# Bottom Bar: y=1085, h=75 (ends at 1160)
# Gap from Note Boxes (1045) to Bottom Bar (1085) is 40px!
# Margin bottom from 1160 to 1200 is 40px!
bot_bar = test_box_padding("Bottom Bar", 40, 1085, 1520, 75, [
    ("Existing partitions are not realigned by the tools, so check them yourself", 26, False, 800, 1132, "middle")
])

print("\n=== OVERALL SUMMARY ===")
all_pass = all([t_ok, row_a_ok, row_a_verdict, row_a_math, row_a_bound,
                row_b_ok, row_b_verdict, row_b_math, row_b_bound, row_b_strad,
                left_note, right_note, bot_bar])
print("ALL PASS:", all_pass)
