import sys

# Test dimensions and text bounds
title = "Lookup order"

# Col 1: x = 60 to 700 (width = 640)
# Col 2: x = 940 to 1540 (width = 600)
# Gap: 700 to 940 = 240 px

# Vertical rows:
# Row 1 (A): y = 90 to 170 (h = 80), centered at col 1 (x = 210 to 550, w = 340)
# Row 2 (B & C): y = 230 to 340 (h = 110)
# Row 3 (D & E): y = 420 to 520 (h = 100)
# Row 4 (F & G): y = 600 to 710 (h = 110)
# Row 5 (H & I): y = 790 to 890 (h = 100)
# Row 6 (J): y = 970 to 1060 (h = 90), centered at col 1 (x = 180 to 580, w = 400)
# Canvas H = 1140 or 1150

print("Rows defined. Let us check label lengths and box boundaries.")

nodes = {
    'A': {
        'box': (190, 90, 380, 80), # x, y, w, h
        'icon': (206, 102, 56, 56),
        'text': [('obj.name', 282, 140, 30, True)] # text, x, y, size, mono
    },
    'B': {
        'box': (60, 230, 640, 110),
        'icon': (80, 257, 56, 56),
        'text': [('name found on type MRO?', 156, 295, 30, False)]
    },
    'C': {
        'box': (940, 230, 600, 110),
        'icon': (960, 257, 56, 56),
        'text': [
            ('descriptor.__get__ (wins over instance dict)', 1036, 295, 26, False)
        ]
    },
    'D': {
        'box': (60, 420, 640, 100),
        'icon': (80, 442, 56, 56),
        'text': [('in instance __dict__?', 156, 482, 30, False)]
    },
    'E': {
        'box': (940, 420, 600, 100),
        'icon': (960, 442, 56, 56),
        'text': [('return instance value', 1036, 482, 30, False)]
    },
    'F': {
        'box': (60, 600, 640, 110),
        'icon': (80, 627, 56, 56),
        'text': [
            ('non-data descriptor or', 156, 645, 28, False),
            ('plain class attr?', 156, 685, 28, False)
        ]
    },
    'G': {
        'box': (940, 600, 600, 110),
        'icon': (960, 627, 56, 56),
        'text': [
            ('descriptor.__get__ / class attr', 1036, 665, 28, False)
        ]
    },
    'H': {
        'box': (60, 790, 640, 100),
        'icon': (80, 812, 56, 56),
        'text': [('__getattr__ defined?', 156, 852, 30, False)]
    },
    'I': {
        'box': (940, 790, 600, 100),
        'icon': (960, 812, 56, 56),
        'text': [('__getattr__(name)', 1036, 852, 30, False)]
    },
    'J': {
        'box': (170, 970, 420, 90),
        'icon': (190, 987, 56, 56),
        'text': [('AttributeError', 266, 1027, 30, False)]
    }
}

for name, data in nodes.items():
    bx, by, bw, bh = data['box']
    ix, iy, iw, ih = data['icon']
    print(f"Node {name}:")
    # check icon inside box
    assert ix >= bx + 10 and iy >= by + 10 and ix + iw <= bx + bw and iy + ih <= by + bh
    for t, tx, ty, sz, mono in data['text']:
        char_w = 0.62 * sz if mono else 0.60 * sz
        est_w = len(t) * char_w
        print(f"  Text '{t}': est width = {est_w:.1f}px, right edge = {tx + est_w:.1f}px, box right = {bx + bw}px")
        assert tx >= ix + iw + 16, f"Text overlaps icon in {name}"
        assert tx + est_w <= bx + bw - 16, f"Text overflows box in {name}: {tx + est_w} > {bx + bw - 16}"

print("All node boxes and texts verified successfully!")
