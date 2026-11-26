c4 = "each line uses the host's ansible_host and its name, so the file follows the inventory: add a host to the inventory, run the playbook, and the new line appears without anyone touching the file"

# Let's wrap into 5 lines with max 36 chars:
def wrap(text, max_chars):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_chars:
            curr.append(w)
            curr_len += len(w) + (1 if len(curr) > 1 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

for l in wrap(c4, 35):
    print(f"[{len(l)} chars, {len(l)*14.4:.1f}px] {l}")
