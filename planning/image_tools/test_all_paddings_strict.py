import math

# We will test all boxes and their text lines

# font metrics:
# sans: 0.60 * fs
# mono: 0.62 * fs

items = [
    # (box_name, bx, by, bw, bh, [(line_text, fs, font, tx, ty)])
    ("Title", 40, 40, 1520, 60, [
        ("When a Service fails, confirm in order", 48, "sans", 800, 88) # text-anchor middle
    ]),
    ("Takeaway", 40, 1104, 1520, 56, [
        ("Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack", 24, "sans", 800, 1142) # middle
    ]),
    ("Small Box", 1190, 140, 370, 92, [
        ("the first failing rung", 24, "sans", 1215, 180),
        ("is where to look", 24, "sans", 1215, 210)
    ]),
    ("Orange Callout", 980, 542, 580, 120, [
        ("ENDPOINTS shows none means", 24, "sans", 1010, 582),
        ("the Service selector does not", 24, "sans", 1010, 610),
        ("match pod labels", 24, "sans", 1010, 638)
    ]),
    ("Rung 1", 160, 140, 990, 92, [
        ("Pod", 30, "sans", 325, 186),
        ("call the pod IP and pod port directly from another pod", 24, "mono", 325, 216)
    ]),
    ("Rung 2", 160, 274, 1400, 92, [
        ("Service", 30, "sans", 325, 320),
        ("the Service exists, otherwise lookup fails with Name or service not known", 24, "mono", 325, 350)
    ]),
    ("Rung 3", 160, 408, 1400, 92, [
        ("DNS", 30, "sans", 325, 454),
        ("short, namespaced and full names resolve", 24, "mono", 325, 484)
    ]),
    ("Rung 4", 160, 542, 780, 120, [
        ("Endpoints", 30, "sans", 325, 588),
        ("kubectl get endpointslices", 24, "mono", 325, 618),
        ("-l kubernetes.io/service-name=hostnames", 24, "mono", 325, 646)
    ]),
    ("Rung 5", 160, 704, 1400, 92, [
        ("Ports", 30, "sans", 325, 750),
        ("Service port listed, targetPort correct, named port matched", 24, "mono", 325, 780)
    ]),
    ("Rung 6", 160, 838, 1400, 92, [
        ("kube-proxy rules", 30, "sans", 325, 884),
        ("iptables-save grep hostnames, or ipvsadm -ln", 24, "mono", 325, 914)
    ]),
    ("Rung 7", 160, 972, 1400, 92, [
        ("Conntrack", 30, "sans", 325, 1018),
        ("table usage, since iptables Service load balancing depends on connection tracking", 24, "mono", 325, 1048)
    ])
]

all_ok = True
for bname, bx, by, bw, bh, lines in items:
    print(f"\n--- Checking {bname} (x={bx}, y={by}, w={bw}, h={bh}) ---")
    for txt, fs, font, tx, ty in lines:
        char_w = 0.62 * fs if font == "mono" else 0.60 * fs
        w = len(txt) * char_w
        
        # Check text alignment
        if bname in ["Title", "Takeaway"]:
            pad_l = (tx - w/2) - bx
            pad_r = (bx + bw) - (tx + w/2)
        else:
            pad_l = tx - bx
            pad_r = (bx + bw) - (tx + w)
            
        pad_t = (ty - fs) - by
        pad_b = (by + bh) - ty
        
        ok = (pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16)
        if not ok:
            all_ok = False
        print(f"[{'PASS' if ok else 'FAIL'}] '{txt[:35]:35s}' | L:{pad_l:5.1f} R:{pad_r:5.1f} T:{pad_t:5.1f} B:{pad_b:5.1f}")

assert all_ok, "Some text failed padding checks!"
print("\nALL TEXT LINES PASS STRICT PADDING CHECKS (>= 16 PX EVERYWHERE)!")
