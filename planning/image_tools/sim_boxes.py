def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

texts = [
    ("Success", "0"),
    ("General error. For grep, diff and cmp: no match or files differ, not an error", "1"),
    ("Misuse of a command, or a real error for grep and diff", "2"),
    ("Found but not executable", "126"),
    ("Command not found", "127"),
    ("Status out of range, or ssh connection failure", "255")
]

for max_c in [18, 20, 22, 24, 26, 28, 30]:
    print(f"\n--- max_chars = {max_c} ---")
    for t, m in texts:
        lines = wrap_text(t, max_c)
        print(f"[{m}] ({len(lines)} lines):")
        for l in lines:
            print(f"    '{l}' (len {len(l)})")

