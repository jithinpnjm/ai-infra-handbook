import xml.etree.ElementTree as ET

# We will test all cards and elements
cards = [
    # (name, box_x, box_y, box_w, box_h, icon_x2, text_x, lines, is_mono, font_size)
    ("node-lookup", 75, 112, 680, 52, 135, 430, ['cfg["timeout"]'], True, 26),
    ("node-layer-1", 75, 184, 680, 52, 135, 155, ['cli_args'], True, 26),
    ("node-layer-2", 75, 256, 680, 74, 135, 155, ['os.environ', '(MYOPS_ prefixed, lowercased)'], True, 24),
    ("node-layer-3", 75, 348, 680, 52, 135, 155, ['file_cfg (/etc/myops.json)'], True, 24),
    ("node-layer-4", 75, 418, 680, 64, 135, 155, ['defaults {retries: 3, timeout: 30}'], True, 24),
    ("node-wins", 75, 500, 680, 54, 135, 430, ['first mapping wins'], False, 26),
    ("node-small-example", 50, 595, 730, 135, 128, 145, [
        'ChainMap({retries: 5},',
        '{retries: 3, timeout: 10}):',
        'cfg[retries] is 5, cfg[timeout] is 10'
    ], True, 24),
    ("node-write-rule", 50, 755, 730, 110, 128, 145, [
        'a write such as chain[c] = -1',
        'changes only the first mapping'
    ], True, 25),
    ("node-cli-note", 50, 890, 730, 175, 128, 145, [
        'CLI values of None are dropped',
        'so they do not hide lower layers:',
        '{k: v for k, v in cli.items()',
        ' if v is not None}'
    ], True, 24),
    ("header-related-views", 820, 95, 730, 970, 906, 925, ['Related views'], False, 34),
    ("rp-item-1", 850, 185, 670, 195, 916, 930, [
        'types.MappingProxyType(d) is a',
        'read-only view that still reflects',
        'later updates to d, so callers cannot',
        'change a hardware pin map while the',
        'owner keeps it current'
    ], False, 24),
    ("rp-item-2", 850, 398, 670, 135, 916, 930, [
        'dict.keys() and dict.items() are live',
        'views with no copying and support',
        '& | - ^'
    ], False, 24),
    ("rp-item-3", 850, 551, 670, 135, 916, 930, [
        'Python scope lookup uses the same',
        'idea: ChainMap(locals(), globals(),',
        'vars(builtins))'
    ], False, 24),
    ("rp-item-4", 850, 704, 670, 135, 916, 930, [
        'merge: a | b, {**a, **b}, or',
        'ChainMap; a deep merge needs',
        'recursion'
    ], False, 24),
    ("rp-item-5", 850, 857, 670, 120, 916, 930, [
        'dicts compare equal regardless of key',
        'order, lists are order-sensitive'
    ], False, 24),
    ("bottom-bar", 50, 1100, 1500, 60, 50, 800, [
        'Use ChainMap when the first mapping should win, without copying'
    ], False, 28)
]

all_passed = True
for name, bx, by, bw, bh, icon_r, tx, lines, is_mono, fs in cards:
    factor = 0.62 if is_mono else 0.60
    box_r = bx + bw
    for line in lines:
        w = len(line) * factor * fs
        if tx == 430 or tx == 800: # centered
            left_t = tx - w/2
            right_t = tx + w/2
        else:
            left_t = tx
            right_t = tx + w
        
        pad_left = left_t - max(bx, icon_r)
        pad_right = box_r - right_t
        
        ok = (pad_left >= 16.0) and (pad_right >= 16.0)
        if not ok:
            print(f"FAIL: {name} line '{line}' | pad_left: {pad_left:.1f}px, pad_right: {pad_right:.1f}px")
            all_passed = False
        else:
            # print(f"PASS: {name} | '{line[:25]}' | L:{pad_left:.1f}px, R:{pad_right:.1f}px")
            pass

print(f"All cards text padding check passed: {all_passed}")
