fn = "for built-in list or str, len(x) reads a size field in the C structure directly in constant time; collections.abc: Iterable needs __iter__, Sized needs __len__, Container needs __contains__; Sequence, Mapping and Set specialise them"

def wrap_text_exact(text, max_w, fs=24):
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test_line = ' '.join(cur + [w])
        if len(test_line) * fs * 0.60 <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
    if cur:
        lines.append(' '.join(cur))
    return lines

lines = wrap_text_exact(fn, 1330, fs=24)
print(f"Footnote lines ({len(lines)}):")
for l in lines:
    w = len(l) * 24 * 0.60
    pad = 1330 - w
    print(f"   w={w:6.1f} | rem={pad:5.1f} px | '{l}'")
    assert pad >= 16.0

joined = ' '.join(lines)
assert joined == fn
print("Footnote exact match verified!")
