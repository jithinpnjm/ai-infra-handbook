# Check that all icons are within their node boxes and do not overlap text
# Box coordinates:
nodes = {
    'A': {'box': (155, 90, 420, 80), 'icon': (175, 102, 56, 56), 'text_x': 251},
    'B': {'box': (50, 230, 630, 110), 'icon': (70, 257, 56, 56), 'text_x': 146},
    'C': {'box': (950, 230, 600, 110), 'icon': (970, 257, 56, 56), 'text_x': 1046},
    'D': {'box': (50, 430, 630, 100), 'icon': (70, 452, 56, 56), 'text_x': 146},
    'E': {'box': (950, 430, 600, 100), 'icon': (970, 452, 56, 56), 'text_x': 1046},
    'F': {'box': (50, 620, 630, 110), 'icon': (70, 647, 56, 56), 'text_x': 146},
    'G': {'box': (950, 620, 600, 110), 'icon': (970, 647, 56, 56), 'text_x': 1046},
    'H': {'box': (50, 820, 630, 100), 'icon': (70, 842, 56, 56), 'text_x': 146},
    'I': {'box': (950, 820, 600, 100), 'icon': (970, 842, 56, 56), 'text_x': 1046},
    'J': {'box': (155, 1010, 420, 90), 'icon': (175, 1027, 56, 56), 'text_x': 251},
}

for name, d in nodes.items():
    bx, by, bw, bh = d['box']
    ix, iy, iw, ih = d['icon']
    tx = d['text_x']
    # Icon within box
    assert ix >= bx + 10 and iy >= by + 5 and ix + iw <= bx + bw and iy + ih <= by + bh
    # Text margin from icon
    assert tx >= ix + iw + 16, f"Text overlaps icon in {name}"
    print(f"Node {name}: icon inside box, text starts {tx - (ix + iw)}px to the right of icon.")

print("All icon positions verified!")
