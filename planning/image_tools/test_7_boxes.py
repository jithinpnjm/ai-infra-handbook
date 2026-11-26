# If 7 boxes across 1520 px:
# 6 gaps of 40 px = 240 px.
# Total width for 7 boxes = 1520 - 240 = 1280 px.

# Can we allocate 1280 px among 7 boxes?
# Let's test widths:
# w0: 120 (for 'Success', 7 chars * 14.4 = 100.8 -> with 16 pad, 100.8 + 32 = 132.8 -> wait, at 26px bold title or 24px: 7 * 14.4 = 101, so 135 px)
# Let's check exact character wrap for each text at various widths!

def test_wrap(text, width, pad=16, fs=24):
    char_w = 0.6 * fs
    inner_w = width - 2 * pad
    max_chars = int(inner_w / char_w)
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if len(w) > max_chars:
            return None, f"Word '{w}' ({len(w)} chars) exceeds max_chars ({max_chars})"
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines, max_chars

texts = [
    ("Success", 120),
    ("General error. For grep, diff and cmp: no match or files differ, not an error", 260),
    ("Misuse of a command, or a real error for grep and diff", 210),
    ("Found but not executable", 170),
    ("Command not found", 160),
    ("Status out of range, or ssh connection failure", 200),
]

for t, w in texts:
    lines, note = test_wrap(t, w)
    print(f"w={w}: {note}")
    if lines:
        for l in lines:
            print(f"   '{l}' ({len(l)} chars, {len(l)*14.4:.1f}px <= {w-32}px)")
    print()

total_w = sum(w for t, w in texts)
print(f"Total width of 6 boxes: {total_w}")
print(f"Remaining for 128+N box from 1280 px: {1280 - total_w}")

