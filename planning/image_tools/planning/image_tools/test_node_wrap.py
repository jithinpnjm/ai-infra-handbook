def test_wrap():
    nodes = [
        ("Client", 180),
        ("anycast or ECMP to a fleet of L4 and L7 gateways (BGP VIP, BFD)", 280),
        ("TLS termination and L7 routing with per-request, per-tenant policy", 290),
        ("load- and cache-aware endpoint picker", 260),
        ("inference pods with readiness, drain and GPU health integration", 290)
    ]
    for text, w in nodes:
        print(f"\n--- Node: {text[:30]}... (width={w}) ---")
        words = text.split()
        lines = []
        curr = []
        for word in words:
            curr.append(word)
            line = " ".join(curr)
            # test line width: len * 0.6 * 24
            if len(line) * 0.6 * 24 > (w - 32):
                curr.pop()
                lines.append(" ".join(curr))
                curr = [word]
        if curr:
            lines.append(" ".join(curr))
        for l in lines:
            lw = len(l) * 0.6 * 24
            print(f"  [{lw:5.1f}px / {w-32}px] '{l}'")

test_wrap()
