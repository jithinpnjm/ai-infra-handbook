def check_all_node_paddings():
    nodes = [
        ("Client", 130, ["Client"]),
        ("anycast or ECMP to a fleet of L4 and L7 gateways (BGP VIP, BFD)", 275, [
            "anycast or ECMP",
            "to a fleet of L4",
            "and L7 gateways",
            "(BGP VIP, BFD)"
        ]),
        ("TLS termination and L7 routing with per-request, per-tenant policy", 285, [
            "TLS termination",
            "and L7 routing",
            "with per-request,",
            "per-tenant policy"
        ]),
        ("load- and cache-aware endpoint picker", 250, [
            "load- and",
            "cache-aware",
            "endpoint picker"
        ]),
        ("inference pods with readiness, drain and GPU health integration", 260, [
            "inference pods",
            "with readiness,",
            "drain and GPU",
            "health",
            "integration"
        ])
    ]
    
    all_ok = True
    for text, w, lines in nodes:
        print(f"\nChecking node w={w} ('{text[:25]}...'):")
        for line in lines:
            lw = len(line) * 0.6 * 24
            pad = (w - lw) / 2
            ok = pad >= 16
            if not ok:
                all_ok = False
            print(f"  [{'OK' if ok else 'FAIL'}] line='{line}', lw={lw:.1f}px, pad={pad:.1f}px")
            
    print(f"\nOverall result: {'ALL PASSED' if all_ok else 'SOME FAILED'}")

check_all_node_paddings()
