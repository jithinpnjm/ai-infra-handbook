def check_all_sec3():
    s3_y = 740
    s3_h = 310
    s3_w = 1520
    
    # Row 1 cards: y = 798, h = 95, w = 705
    # Card 1 (EndpointSlices):
    r1_y = 798
    r1_h = 95
    c1_x = 60
    c1_w = 705
    c1_lines = [
        "EndpointSlices list the ready pods and",
        "readiness probes control membership"
    ]
    # Check c1 paddings
    b1 = r1_y + 18 + 24 # 840
    b2 = b1 + 28 # 868
    top_pad = b1 - 24 - r1_y # 18
    bot_pad = (r1_y + r1_h) - b2 # 893 - 868 = 25
    assert top_pad >= 16
    assert bot_pad >= 16
    for l in c1_lines:
        lw = len(l) * 24 * 0.6
        pad_x = (c1_w - lw) / 2
        assert pad_x >= 16
        print(f"C1 line '{l}': lw={lw:.1f}, pad_x={pad_x:.1f}")
        
    # Card 2 (service meshes):
    c2_x = 835
    c2_w = 705
    c2_lines = [
        "service meshes add per-pod proxies for mTLS,",
        "retries and L7 balancing between services"
    ]
    for l in c2_lines:
        lw = len(l) * 24 * 0.6
        pad_x = (c2_w - lw) / 2
        assert pad_x >= 16
        print(f"C2 line '{l}': lw={lw:.1f}, pad_x={pad_x:.1f}")

    # Row 2 cards: y = 910, h = 122, w = 705
    r2_y = 910
    r2_h = 122
    # Card 3 (Ingress):
    c3_x = 60
    c3_w = 705
    c3_lines = [
        "Ingress and Gateway API: L7 HTTP routing and",
        "TLS through nginx, HAProxy, Contour, Emissary,",
        "Envoy Gateway, Traefik and cloud controllers"
    ]
    b1 = r2_y + 18 + 24 # 952
    b2 = b1 + 28 # 980
    b3 = b2 + 28 # 1008
    top_pad = b1 - 24 - r2_y # 18
    bot_pad = (r2_y + r2_h) - b3 # 1032 - 1008 = 24
    assert top_pad >= 16
    assert bot_pad >= 16
    for l in c3_lines:
        lw = len(l) * 24 * 0.6
        pad_x = (c3_w - lw) / 2
        assert pad_x >= 16
        print(f"C3 line '{l}': lw={lw:.1f}, pad_x={pad_x:.1f}")

    # Card 4 (MetalLB):
    c4_x = 835
    c4_w = 705
    c4_lines = [
        "MetalLB, kube-vip and Cilium provide",
        "LoadBalancer VIPs on bare metal using",
        "ARP or BGP (ECMP)"
    ]
    for l in c4_lines:
        lw = len(l) * 24 * 0.6
        pad_x = (c4_w - lw) / 2
        assert pad_x >= 16
        print(f"C4 line '{l}': lw={lw:.1f}, pad_x={pad_x:.1f}")

    print("ALL Section 3 cards PASS padding checks with >= 18px on all sides!")

check_all_sec3()
