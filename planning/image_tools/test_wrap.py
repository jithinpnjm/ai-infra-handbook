def wrap(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return lines

docker_note = "almost literally what the default bridge network does: docker0, a veth per container, an IPAM address from a private pool, a default route via the bridge, masquerade, DNAT for published ports, a bind-mounted /etc/resolv.conf"
for max_c in [50, 55, 60, 100, 110]:
    res = wrap(docker_note, max_c)
    print(f"max_chars={max_c}, lines={len(res)}:")
    for l in res:
        print("  ", l)
