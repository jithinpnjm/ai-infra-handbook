def calc_w(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text.strip()) * factor * fs

# Left column items:
# 1. interval: how often (y = 215, h = 75)
# 2. timeout: how long to wait (y = 300, h = 95)
# 3. fall: failures needed to mark down (y = 405, h = 95)
# 4. rise: successes needed to mark up (y = 510, h = 95)
# 5. worked line (y = 615, h = 150)
# 6. warning 1 (y = 775, h = 145)
# 7. warning 2 (y = 930, h = 145)

box_right = 500 # 60 + 440

for label, lines, fs, x in [
    ("interval", ["interval: how often"], 25, 120),
    ("timeout", ["timeout: ", "how long to wait"], 25, 120),
    ("fall", ["fall: failures needed ", "to mark down"], 25, 120),
    ("rise", ["rise: successes needed ", "to mark up"], 25, 120),
]:
    for l in lines:
        w = calc_w(l, fs)
        right = x + w
        pad_right = box_right - right
        pad_left = x - 60
        print(f"{label} line '{l}': left pad={pad_left}, right pad={pad_right:.1f} (fs={fs})")
        assert pad_left >= 16 and pad_right >= 16
print("ALL SUB-CARDS IN COL 1 PASS PADDING!")
