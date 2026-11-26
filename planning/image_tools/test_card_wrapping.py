def w_sans(s, fs=24): return len(s) * 0.6 * fs
def w_mono(s, fs=24): return len(s) * 0.62 * fs

def check_lines(name, lines, max_w=660, is_mono=False):
    print(f"=== {name} ===")
    all_ok = True
    for l in lines:
        w = w_mono(l) if is_mono else w_sans(l)
        pad = (max_w - w) / 2
        ok = pad >= 16
        if not ok: all_ok = False
        print(f"  [{'OK' if ok else 'FAIL'}] pad={pad:4.1f}px, w={w:5.1f}px: '{l}'")
    return all_ok

# Card width inside 740px panel:
# Panel x=40, w=740. Card x=60, w=700.
# Available width inside card = 700. Min padding 16 each side means max text width = 700 - 32 = 668px.
# If text is left aligned at x=80, padding left is 20px, so max text width = 700 - 40 = 660px!

# Traps 1:
# "locale.getpreferredencoding() changes with the environment; containers that set LANG=C surprise people; always pass encoding=\"utf-8\" to open()"
t1_lines = [
    "locale.getpreferredencoding() changes with the environment;",
    "containers that set LANG=C surprise people;",
    "always pass encoding=\"utf-8\" to open()"
]
check_lines("Trap 1", t1_lines)

# Traps 2:
# "the same visible text can have different code point sequences: é as one code point or e plus a combining accent; normalise both with unicodedata.normalize(\"NFC\", s) before comparing"
t2_lines = [
    "the same visible text can have different code point sequences:",
    "é as one code point or e plus a combining accent;",
    "normalise both with unicodedata.normalize(\"NFC\", s)",
    "before comparing"
]
check_lines("Trap 2", t2_lines)

# Traps 3:
# "str.casefold() for caseless matching"
t3_lines = ["str.casefold() for caseless matching"]
check_lines("Trap 3", t3_lines)

# Traps 4:
# "len() counts code points, not bytes or graphemes"
t4_lines = ["len() counts code points, not bytes or graphemes"]
check_lines("Trap 4", t4_lines)

# Traps 5:
# "sorting follows code point order; use locale.strxfrm or ICU for human order"
t5_lines = [
    "sorting follows code point order;",
    "use locale.strxfrm or ICU for human order"
]
check_lines("Trap 5", t5_lines)

# Encodings:
# "UTF-8 default for new work, ASCII is a subset, Latin-1 maps bytes one to one onto code points 0 to 255 which carries arbitrary bytes through text APIs"
e1_lines = [
    "UTF-8 default for new work, ASCII is a subset,",
    "Latin-1 maps bytes one to one onto code points 0 to 255",
    "which carries arbitrary bytes through text APIs"
]
check_lines("Encodings", e1_lines)

# Bytes facts 1:
# "b\"abc\"[0] == 97 indexing bytes returns integers"
b1_lines = ["b\"abc\"[0] == 97 indexing bytes returns integers"]
check_lines("Bytes facts 1", b1_lines)

# Bytes facts 2:
# "bytes.hex(), bytes.fromhex, int.from_bytes, struct.pack and unpack for binary protocols, base64, hashlib"
b2_lines = [
    "bytes.hex(), bytes.fromhex, int.from_bytes,",
    "struct.pack and unpack for binary protocols, base64, hashlib"
]
check_lines("Bytes facts 2", b2_lines)
