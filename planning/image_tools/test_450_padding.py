"""Verify 450x140 boxes padding strictly."""

bw = 450
bh = 140
rel_x = 84

from test_perfect_wraps import nodes_config_30

nodes_config_30['EV']['y_start'] = 39
nodes_config_30['A']['y_start'] = 39
nodes_config_30['U']['y_start'] = 39

all_pass = True
for nid, cfg in nodes_config_30.items():
    y_start = cfg['y_start']
    dy = cfg['dy']
    lines = cfg['text']
    for i, (line_text, fs, weight) in enumerate(lines):
        tw = len(line_text) * 0.60 * fs
        pad_R = bw - (rel_x + tw)
        y_curr = y_start + i * dy
        if i == 0: box_pad_T = y_curr - fs * 0.75
        if i == len(lines) - 1: box_pad_B = bh - y_curr
        if pad_R < 16.0:
            print(f"FAIL PAD_R: {nid} line '{line_text}': tw={tw}, pad_R={pad_R} < 16.0")
            all_pass = False
    if box_pad_T < 16.0 or box_pad_B < 16.0:
        print(f"FAIL PAD_V: {nid}: pad_T={box_pad_T}, pad_B={box_pad_B}")
        all_pass = False
    print(f"{nid:5s}: pad_L={rel_x:4.1f}, pad_R={pad_R:4.1f}, pad_T={box_pad_T:4.1f}, pad_B={box_pad_B:4.1f}")

assert all_pass, "Some padding failed!"
print("\nALL 14 NODES HAVE >= 16.0px PADDING ON ALL 4 SIDES!")
