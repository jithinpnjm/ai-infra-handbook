import xml.etree.ElementTree as ET

# Exact padding check
boxes = [
    {
        "name": "Box 1 (HPA)",
        "box": (55, 140, 550, 80),
        "align": "left",
        "lines": [
            ("HPA asks for more replicas", 24, 188, 145, False)
        ]
    },
    {
        "name": "Box 2 (Pending)",
        "box": (55, 260, 550, 100),
        "align": "left",
        "lines": [
            ("pods sit Pending:", 24, 306, 145, False),
            ("no node has a free GPU", 24, 334, 145, False)
        ]
    },
    {
        "name": "Box 3 (CA notices)",
        "box": (55, 400, 550, 126),
        "align": "left",
        "lines": [
            ("cluster autoscaler notices", 24, 446, 145, False),
            ("pending pods that a node", 24, 474, 145, False),
            ("group could fit", 24, 502, 145, False)
        ]
    },
    {
        "name": "Box 4 (Cloud asks)",
        "box": (55, 566, 550, 100),
        "align": "left",
        "lines": [
            ("asks the cloud for a node;", 24, 612, 145, False),
            ("provisioning clock starts", 24, 640, 145, False)
        ]
    },
    {
        "name": "Box 5 (Ready)",
        "box": (55, 706, 550, 100),
        "align": "left",
        "lines": [
            ("node registers, image pull,", 24, 752, 145, False),
            ("weight load, ready", 24, 780, 145, False)
        ]
    },
    {
        "name": "Dashboard Note",
        "box": (55, 836, 550, 164),
        "align": "left",
        "lines": [
            ("replica count rose at", 24, 880, 145, False),
            ("once while serving", 24, 908, 145, False),
            ("count stayed flat;", 24, 936, 145, False),
            ("that gap is what to explain", 24, 964, 145, False)
        ]
    },
    {
        "name": "Card 1 (Expander)",
        "box": (675, 140, 870, 126),
        "align": "left",
        "lines": [
            ("expander chooses which node group to grow:", 24, 187, 746, False),
            ("random, most-pods, least-waste, price,", 24, 215, 746, False),
            ("priority (rank GPU types)", 24, 243, 746, False)
        ]
    },
    {
        "name": "Card 2 (Provision Time)",
        "box": (675, 290, 870, 150),
        "align": "left",
        "lines": [
            ("--max-node-provision-time default 15 minutes:", 24, 334, 746, True),
            ("if a node has not registered by then", 24, 362, 746, False),
            ("the autoscaler stops counting it,", 24, 390, 746, False),
            ("which is why you keep warm capacity", 24, 418, 746, False)
        ]
    },
    {
        "name": "Card 3 (Scale Down)",
        "box": (675, 460, 870, 260),
        "align": "left",
        "lines": [
            ("scale-down: node considered when pod CPU and", 24, 504, 746, False),
            ("memory requests sum below 50 percent of allocatable;", 24, 532, 746, False),
            ("must stay unneeded 10 minutes; held 10 minutes after a", 24, 560, 746, False),
            ("scale-up; evicts through the eviction API for up to", 24, 588, 746, False),
            ("2 minutes; accelerator flag", 24, 616, 746, False),
            ("scale-down-gpu-utilization-threshold default 0.5", 24, 644, 746, True)
        ]
    },
    {
        "name": "Card 4 (Nebius)",
        "box": (675, 775, 870, 225),
        "align": "left",
        "lines": [
            ("autoscaling min and max node count flags; page gives", 24, 817, 746, False),
            ("no defaults or timings; keep a CPU node group of at", 24, 845, 746, False),
            ("least two nodes (or autoscaling) so CoreDNS and", 24, 873, 746, False),
            ("networking add-ons run there; known issue with", 24, 901, 746, False),
            ("GPU Operator and Network Operator creating", 24, 929, 746, False),
            ("extra nodes, not reproduced", 24, 957, 746, False)
        ]
    }
]

all_pass = True
for b in boxes:
    bx, by, bw, bh = b["box"]
    align = b.get("align", "left")
    print(f"\nChecking {b['name']}: box=({bx}, {by}, {bw}, {bh})")
    for txt, fs, baseline, anchor_x, is_mono in b["lines"]:
        line_w = len(txt) * fs * (0.62 if is_mono else 0.6)
        if align == "middle":
            t_left = anchor_x - line_w / 2
            t_right = anchor_x + line_w / 2
        else:
            t_left = anchor_x
            t_right = anchor_x + line_w
        
        pad_l = t_left - bx
        pad_r = (bx + bw) - t_right
        pad_t = (baseline - fs) - by
        pad_b = (by + bh) - baseline
        
        ok_l = pad_l >= 16
        ok_r = pad_r >= 16
        ok_t = pad_t >= 16
        ok_b = pad_b >= 16
        
        if not (ok_l and ok_r and ok_t and ok_b):
            all_pass = False
            print(f"  FAILED: '{txt}'")
            print(f"    pad_l={pad_l:.1f} ({ok_l}), pad_r={pad_r:.1f} ({ok_r}), pad_t={pad_t:.1f} ({ok_t}), pad_b={pad_b:.1f} ({ok_b})")
        else:
            print(f"  OK: '{txt[:35]}...' pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")

assert all_pass, "Some boxes failed padding check!"
print("\n>>> ALL 10 BOXES AND ALL 31 LINES PASSED STRICT >= 16PX PADDING AUDIT! <<<")
