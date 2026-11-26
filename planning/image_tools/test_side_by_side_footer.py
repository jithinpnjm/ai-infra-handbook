# If Footer has DNS inside on left, Docker note on right:
# Let's check text fits:
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

dns = "DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf"
docker = "almost literally what the default bridge network does: docker0, a veth per container, an IPAM address from a private pool, a default route via the bridge, masquerade, DNAT for published ports, a bind-mounted /etc/resolv.conf"

print("DNS (max 45 chars):")
dns_l = wrap(dns, 45)
for l in dns_l:
    print(f"  ({len(l)}) {l} -> {len(l)*24*0.62:.1f}px")

print("\nDocker (max 55 chars):")
doc_l = wrap(docker, 55)
for l in doc_l:
    print(f"  ({len(l)}) {l} -> {len(l)*24*0.6:.1f}px")
