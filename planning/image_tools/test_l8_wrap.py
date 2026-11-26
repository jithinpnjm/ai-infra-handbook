def wrap(text, max_len):
    words = text.split()
    lines = []
    curr = []
    curr_len = 0
    for w in words:
        if curr_len + len(w) + (1 if curr else 0) <= max_len:
            curr.append(w)
            curr_len += len(w) + (1 if curr_len > 0 else 0)
        else:
            lines.append(" ".join(curr))
            curr = [w]
            curr_len = len(w)
    if curr:
        lines.append(" ".join(curr))
    return lines

l8 = "subclassing a built-in C type such as dict or list directly is risky because C methods ignore Python overrides; use collections.UserDict, UserList or UserString"

for max_l in range(32, 40):
    lines = wrap(l8, max_l)
    print(f"max_l={max_l}, lines={len(lines)}: max len={max(len(l) for l in lines)}")
    for l in lines:
        print("  ", l)
    print()
