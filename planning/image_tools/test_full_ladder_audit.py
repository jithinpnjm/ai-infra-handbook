import re

# Test exact parameters
# Canvas: 1600 x 1200
# Arrow line: x1=55, y1=140, x2=55, y2=1064
# Arrow text: x=68, y=580
# Ladder starts at x = 175
# Number circle: cx=215, cy=by+46, r=24
# Icon: x=250..306, y=by+18 (or by+32), w=56, h=56
# Text starts at x = 325

# Rungs:
# Rung 1: x=175, y=140, w=975, h=92 (ends at 1150)
# Small Box: x=1190, y=140, w=370, h=92 (ends at 1560)
# Rung 2: x=175, y=274, w=1385, h=92 (ends at 1560)
# Rung 3: x=175, y=408, w=1385, h=92 (ends at 1560)
# Rung 4: x=175, y=542, w=765, h=120 (ends at 940)
# Orange Callout: x=980, y=542, w=580, h=120 (ends at 1560)
# Rung 5: x=175, y=704, w=1385, h=92 (ends at 1560)
# Rung 6: x=175, y=838, w=1385, h=92 (ends at 1560)
# Rung 7: x=175, y=972, w=1385, h=92 (ends at 1560)
# Takeaway: x=40, y=1100, w=1520, h=60 (ends at 1160)

items = [
    ("Takeaway", 40, 1100, 1520, 60, [
        ("Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack", 24, "sans", 800, 1144)
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
    ("Rung 1", 175, 140, 975, 92, [
        ("Pod", 30, "sans", 325, 186),
        ("call the pod IP and pod port directly from another pod", 24, "mono", 325, 216)
    ]),
    ("Rung 2", 175, 274, 1385, 92, [
        ("Service", 30, "sans", 325, 320),
        ("the Service exists, otherwise lookup fails with Name or service not known", 24, "mono", 325, 350)
    ]),
    ("Rung 3", 175, 408, 1385, 92, [
        ("DNS", 30, "sans", 325, 454),
        ("short, namespaced and full names resolve", 24, "mono", 325, 484)
    ]),
    ("Rung 4", 175, 542, 765, 120, [
        ("Endpoints", 30, "sans", 325, 588),
        ("kubectl get endpointslices", 24, "mono", 325, 618),
        ("-l kubernetes.io/service-name=hostnames", 24, "mono", 325, 646)
    ]),
    ("Rung 5", 175, 704, 1385, 92, [
        ("Ports", 30, "sans", 325, 750),
        ("Service port listed, targetPort correct, named port matched", 24, "mono", 325, 780)
    ]),
    ("Rung 6", 175, 838, 1385, 92, [
        ("kube-proxy rules", 30, "sans", 325, 884),
        ("iptables-save grep hostnames, or ipvsadm -ln", 24, "mono", 325, 914)
    ]),
    ("Rung 7", 175, 972, 1385, 92, [
        ("Conntrack", 30, "sans", 325, 1018),
        ("table usage, since iptables Service load balancing depends on connection tracking", 24, "mono", 325, 1048)
    ])
]

all_ok = True
for bname, bx, by, bw, bh, lines in items:
    print(f"\n--- Checking {bname} ---")
    for txt, fs, font, tx, ty in lines:
        char_w = 0.62 * fs if font == "mono" else 0.60 * fs
        w = len(txt) * char_w
        if bname == "Takeaway":
            pad_l = (tx - w/2) - bx
            pad_r = (bx + bw) - (tx + w/2)
        else:
            pad_l = tx - bx
            pad_r = (bx + bw) - (tx + w)
            
        pad_t = (ty - fs) - by
        pad_b = (by + bh) - ty
        
        ok = (pad_l >= 16.0 and pad_r >= 16.0 and pad_t >= 16.0 and pad_b >= 16.0)
        if not ok:
            all_ok = False
        print(f"[{'PASS' if ok else 'FAIL'}] '{txt[:35]:35s}' | L:{pad_l:5.1f} R:{pad_r:5.1f} T:{pad_t:5.1f} B:{pad_b:5.1f}")

assert all_ok, "Some text failed padding checks!"
print("\nALL BOXES AND TEXT PASS STRICT PADDING AUDIT PERFECTLY!")
