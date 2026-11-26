def w_sans(s, fs=24): return len(s) * 0.6 * fs
def w_mono(s, fs=24): return len(s) * 0.62 * fs

checks = [
    # (label, text, box_w, box_x, text_x, align, fs, mono)
    ("Pipeline Left line 1", "bytes in:", 330, 50, 215, "middle", 24, False),
    ("Pipeline Left line 2", "file in binary mode,", 330, 50, 215, "middle", 24, False),
    ("Pipeline Left line 3", "socket reads,", 330, 50, 215, "middle", 24, False),
    ("Pipeline Left line 4", "subprocess output", 330, 50, 215, "middle", 24, False),

    ("Arrow 1 line 1", 'data.decode("utf-8")', 330, 380, 545, "middle", 24, True),
    ("Arrow 1 line 2", 'when input arrives', 330, 380, 545, "middle", 24, False),

    ("Pipeline Mid line 1", "str: Unicode text", 360, 710, 890, "middle", 24, False),
    ("Pipeline Mid line 2", "(code points);", 360, 710, 890, "middle", 24, False),
    ("Pipeline Mid line 3", "JSON, YAML and regular", 360, 710, 890, "middle", 24, False),
    ("Pipeline Mid line 4", "expressions work here", 360, 710, 890, "middle", 24, False),

    ("Arrow 2 line 1", 's.encode("utf-8")', 300, 1070, 1220, "middle", 24, True),
    ("Arrow 2 line 2", 'when output leaves', 300, 1070, 1220, "middle", 24, False),

    ("Pipeline Right line 1", "bytes out", 180, 1370, 1460, "middle", 24, False),

    ("Errors row", "strict, replace, ignore, surrogateescape, backslashreplace", 1480, 60, 800, "middle", 24, True),

    ("Trap 1 line 1", "locale.getpreferredencoding() changes with", 700, 60, 80, "start", 24, False),
    ("Trap 1 line 2", "the environment; containers that set", 700, 60, 80, "start", 24, False),
    ("Trap 1 line 3", "LANG=C surprise people; always pass", 700, 60, 80, "start", 24, False),
    ("Trap 1 line 4", 'encoding="utf-8" to open()', 700, 60, 80, "start", 24, False),

    ("Trap 2 line 1", "the same visible text can have different", 700, 60, 80, "start", 24, False),
    ("Trap 2 line 2", "code point sequences: é as one code point", 700, 60, 80, "start", 24, False),
    ("Trap 2 line 3", "or e plus a combining accent; normalise", 700, 60, 80, "start", 24, False),
    ("Trap 2 line 4", 'both with unicodedata.normalize("NFC", s)', 700, 60, 80, "start", 24, False),
    ("Trap 2 line 5", "before comparing", 700, 60, 80, "start", 24, False),

    ("Trap 3 line 1", "str.casefold() for caseless matching", 700, 60, 80, "start", 24, False),

    ("Trap 4 line 1", "len() counts code points, not bytes or", 700, 60, 80, "start", 24, False),
    ("Trap 4 line 2", "graphemes", 700, 60, 80, "start", 24, False),

    ("Trap 5 line 1", "sorting follows code point order; use", 700, 60, 80, "start", 24, False),
    ("Trap 5 line 2", "locale.strxfrm or ICU for human order", 700, 60, 80, "start", 24, False),

    ("Encodings line 1", "UTF-8 default for new work, ASCII is a", 700, 840, 860, "start", 24, False),
    ("Encodings line 2", "subset, Latin-1 maps bytes one to one onto", 700, 840, 860, "start", 24, False),
    ("Encodings line 3", "code points 0 to 255 which carries", 700, 840, 860, "start", 24, False),
    ("Encodings line 4", "arbitrary bytes through text APIs", 700, 840, 860, "start", 24, False),

    ("Bytes fact 1 line 1", 'b"abc"[0] == 97 indexing bytes returns', 700, 840, 860, "start", 24, False),
    ("Bytes fact 1 line 2", 'integers', 700, 840, 860, "start", 24, False),

    ("Bytes fact 2 line 1", 'bytes.hex(), bytes.fromhex,', 700, 840, 860, "start", 24, False),
    ("Bytes fact 2 line 2", 'int.from_bytes, struct.pack and unpack for', 700, 840, 860, "start", 24, False),
    ("Bytes fact 2 line 3", 'binary protocols, base64, hashlib', 700, 840, 860, "start", 24, False),

    ("Bottom bar", 'Convert only at the boundaries of your program', 1520, 40, 800, "middle", 28, False),
]

all_ok = True
print("=== CHECKING ALL TEXT PADDINGS CONSERVATIVELY ===")
for name, text, box_w, box_x, text_x, align, fs, mono in checks:
    w = w_mono(text, fs) if mono else w_sans(text, fs)
    if align == "middle":
        pad_left = (text_x - w/2) - box_x
        pad_right = (box_x + box_w) - (text_x + w/2)
    else:
        pad_left = text_x - box_x
        pad_right = (box_x + box_w) - (text_x + w)
    min_pad = min(pad_left, pad_right)
    ok = (min_pad >= 16.0)
    if not ok: all_ok = False
    print(f"  [{'OK' if ok else 'FAIL'}] min_pad={min_pad:5.1f}px (left={pad_left:5.1f}, right={pad_right:5.1f}, w={w:5.1f}): {name}")

assert all_ok, "Some paddings failed min_pad >= 16.0!"
print("\nEVERY SINGLE LINE HAS >= 16px PADDING!")
