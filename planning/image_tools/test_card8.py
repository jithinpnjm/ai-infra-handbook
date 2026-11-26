def wrap_text_exact(text, max_w, fs=24, is_mono=False):
    char_w = fs * (0.62 if is_mono else 0.60)
    words = text.split()
    lines = []
    cur = []
    for w in words:
        test_line = ' '.join(cur + [w])
        if len(test_line) * char_w <= max_w:
            cur.append(w)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
    if cur:
        lines.append(' '.join(cur))
    return lines

lines8 = wrap_text_exact(
    "Node(07, r2) in inv is True, Node(07, r9) in inv is False (a sequential scan)",
    378,
    fs=24
)
print(f"Card 8 has {len(lines8)} lines at usable 378:")
for l in lines8:
    w = len(l) * 24 * 0.6
    print(f"   w={w:5.1f} | pad={(410-w)/2:4.1f} px | '{l}'")
