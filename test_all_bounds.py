nodes = {
    'A': {
        'box': (170, 90, 420, 80),
        'icon': (190, 102, 56, 56),
        'text': [('obj.name', 266, 140, 30, True)]
    },
    'B': {
        'box': (60, 230, 640, 110),
        'icon': (80, 257, 56, 56),
        'text': [('name found on type MRO?', 156, 295, 30, False)]
    },
    'C': {
        'box': (920, 230, 620, 110),
        'icon': (940, 257, 56, 56),
        'text': [
            ('descriptor.__get__', 1016, 275, 28, True),
            ('(wins over instance dict)', 1016, 315, 26, False)
        ]
    },
    'D': {
        'box': (60, 420, 640, 100),
        'icon': (80, 442, 56, 56),
        'text': [('in instance __dict__?', 156, 482, 30, False)]
    },
    'E': {
        'box': (920, 420, 620, 100),
        'icon': (940, 442, 56, 56),
        'text': [('return instance value', 1016, 482, 30, False)]
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
        'box': (920, 600, 620, 110),
        'icon': (940, 627, 56, 56),
        'text': [
            ('descriptor.__get__ /', 1016, 645, 28, True),
            ('class attr', 1016, 685, 28, False)
        ]
    },
    'H': {
        'box': (60, 790, 640, 100),
        'icon': (80, 812, 56, 56),
        'text': [('__getattr__ defined?', 156, 852, 30, False)]
    },
    'I': {
        'box': (920, 790, 620, 100),
        'icon': (940, 812, 56, 56),
        'text': [('__getattr__(name)', 1016, 852, 30, True)]
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
    assert ix >= bx + 10 and iy >= by + 10 and ix + iw <= bx + bw and iy + ih <= by + bh
    for t, tx, ty, sz, mono in data['text']:
        char_w = 0.62 * sz if mono else 0.60 * sz
        est_w = len(t) * char_w
        margin_left = tx - (ix + iw)
        margin_right = (bx + bw) - (tx + est_w)
        print(f"  '{t}': sz={sz}, w={est_w:.1f}px, left_pad={margin_left:.1f}px, right_pad={margin_right:.1f}px")
        assert margin_left >= 16, f"Text overlaps icon in {name}"
        assert margin_right >= 16, f"Text overflows box in {name}"

print("\nAll nodes passed perfectly!")
