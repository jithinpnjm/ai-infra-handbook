def wrap_text(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            if cur:
                lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return lines

labels_left = [
    "Did the server receive the request?",
    "Did the request leave the client at all?",
    "Traffic inside a pod",
    "Traffic crossing between namespaces",
    "Need the wire itself, independent of the host stack",
    "RoCE or traffic the kernel does not see",
    "Where was the packet dropped, without copying it?"
]

# If left box width is 640.
# Left margin to icon = 20, icon = 50, gap = 20 -> text starts at 90 from box left.
# Available text width = 640 - 90 - 20 (right pad) = 530 px.
# At 30px (0.6 * 30 = 18 px/char): max chars = 530 / 18 = 29.4 chars.
# Say max 28 chars.
print("=== LEFT COLUMN at 30px (max 28 chars) ===")
for ll in labels_left:
    lines = wrap_text(ll, 28)
    print(f"Original: '{ll}'")
    for line in lines:
        w = len(line) * 18
        print(f"   [{len(line)} chars, {w:.1f}px] : '{line}'")

