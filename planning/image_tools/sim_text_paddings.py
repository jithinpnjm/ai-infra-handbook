import re

# Font size: 24 for normal text, 25 or 26 for short titles
# For font-size fs:
# Text top is approximately baseline - 0.75 * fs
# Text bottom is approximately baseline + 0.25 * fs (or baseline for caps)
# With dy=28 (or 30), total height for n lines is (n-1)*dy + fs.

def calc_text_block(lines, fs, dy, box_y, box_h):
    n = len(lines)
    text_h = (n - 1) * dy + fs
    # Center the text block vertically in the box:
    # top_pad = (box_h - text_h) / 2
    top_pad = (box_h - text_h) / 2
    # baseline of first line = box_y + top_pad + 0.78 * fs
    base_y = box_y + top_pad + 0.78 * fs
    bot_pad = box_h - (top_pad + text_h)
    return base_y, top_pad, bot_pad

# Let us test all rows:
from sim_autoscaling import rows, row_positions

for r, ry in row_positions:
    rh = r["h"]
    print(f"=== {r['id']} (y={ry}, h={rh}) ===")
    
    # Col 1
    c1_fs = 26 if len(r["c1"]) == 1 else 24
    c1_dy = 32 if len(r["c1"]) == 1 else 30
    b1, tp1, bp1 = calc_text_block(r["c1"], c1_fs, c1_dy, ry, rh)
    print(f"  Col 1 ({len(r['c1'])} lines, fs={c1_fs}): base_y={b1:.1f}, top_pad={tp1:.1f}, bot_pad={bp1:.1f}")
    assert tp1 >= 16, f"Col 1 top_pad < 16: {tp1}"
    assert bp1 >= 16, f"Col 1 bot_pad < 16: {bp1}"
    
    # Col 2
    c2_fs = 24
    c2_dy = 28
    b2, tp2, bp2 = calc_text_block(r["c2"], c2_fs, c2_dy, ry, rh)
    print(f"  Col 2 ({len(r['c2'])} lines, fs={c2_fs}): base_y={b2:.1f}, top_pad={tp2:.1f}, bot_pad={bp2:.1f}")
    assert tp2 >= 16, f"Col 2 top_pad < 16: {tp2}"
    assert bp2 >= 16, f"Col 2 bot_pad < 16: {bp2}"
    
    # Col 3
    c3_fs = 24
    c3_dy = 28
    b3, tp3, bp3 = calc_text_block(r["c3"], c3_fs, c3_dy, ry, rh)
    print(f"  Col 3 ({len(r['c3'])} lines, fs={c3_fs}): base_y={b3:.1f}, top_pad={tp3:.1f}, bot_pad={bp3:.1f}")
    assert tp3 >= 16, f"Col 3 top_pad < 16: {tp3}"
    assert bp3 >= 16, f"Col 3 bot_pad < 16: {bp3}"

print("\nALL VERTICAL PADDINGS STRICTLY >= 16 PX!")
