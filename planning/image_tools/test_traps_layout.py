def w_sans(s, fs=24): return len(s) * 0.6 * fs

# Traps panel: x=40, y=425, w=740, h=620
# Card x=60, w=700 (pad left/right = 20px)

cards = [
    {
        "name": "Trap 1",
        "lines": [
            'locale.getpreferredencoding() changes with',
            'the environment; containers that set',
            'LANG=C surprise people; always pass',
            'encoding="utf-8" to open()'
        ]
    },
    {
        "name": "Trap 2",
        "lines": [
            'the same visible text can have different',
            'code point sequences: é as one code point',
            'or e plus a combining accent; normalise',
            'both with unicodedata.normalize("NFC", s)',
            'before comparing'
        ]
    },
    {
        "name": "Trap 3",
        "lines": [
            'str.casefold() for caseless matching'
        ]
    },
    {
        "name": "Trap 4",
        "lines": [
            'len() counts code points, not bytes or',
            'graphemes'
        ]
    },
    {
        "name": "Trap 5",
        "lines": [
            'sorting follows code point order; use',
            'locale.strxfrm or ICU for human order'
        ]
    }
]

# Lets calculate heights and y positions
y = 445 # start inside panel (panel top is 425, pad 20px)
for c in cards:
    n_lines = len(c["lines"])
    # text height = (n_lines - 1) * 28 + 24
    # with 16px top and bottom padding:
    # card_h = (n_lines - 1) * 28 + 24 + 32 = n_lines * 28 + 28
    card_h = n_lines * 28 + 28
    c["y"] = y
    c["h"] = card_h
    print(f"{c[\x27name\x27]}: lines={n_lines}, y={y}, h={card_h}, bottom={y+card_h}")
    y += card_h + 12 # 12px gap between cards

print(f"Total height used: {y - 425}px (panel height is 620px, remaining: {620 - (y - 425)}px)")
