def w_sans(s, fs=24): return len(s) * 0.6 * fs
def w_mono(s, fs=24): return len(s) * 0.62 * fs

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr and curr_len + 1 + len(w) > max_chars:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
        else:
            curr.append(w)
            curr_len = curr_len + (1 if curr_len > 0 else 0) + len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

traps = [
    'locale.getpreferredencoding() changes with the environment; containers that set LANG=C surprise people; always pass encoding="utf-8" to open()',
    'the same visible text can have different code point sequences: é as one code point or e plus a combining accent; normalise both with unicodedata.normalize("NFC", s) before comparing',
    'str.casefold() for caseless matching',
    'len() counts code points, not bytes or graphemes',
    'sorting follows code point order; use locale.strxfrm or ICU for human order',
]

print("=== Wrapping for 700px box (max_chars ~ 42) ===")
for i, t in enumerate(traps, 1):
    lines = wrap_text(t, 42)
    print(f"Trap {i} ({len(lines)} lines):")
    for l in lines:
        w = w_sans(l)
        print(f"    '{l}' -> {w:.1f}px (pad in 700px: {(700-w)/2:.1f}px)")
