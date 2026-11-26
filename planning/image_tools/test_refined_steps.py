#!/usr/bin/env python3
import sys

# Refined step coordinates and checks
# Let's test all 14 steps with the refined layout

refined_steps = [
    # 1. U->>C: sbatch job.sh (RPC with munge credential)
    {
        "num": 1, "src": "U", "dst": "C", "y": 230,
        "circle": (180, 230),
        "arrow": ("msg_right", 204, 490, 230),
        "card": (214, 194, 640, 32, "#ffffff", "#207448"),
        "text_type": "inline",
        "text": [
            ("sbatch job.sh", True),
            (" (RPC with munge credential)", False)
        ],
        "tx": 234, "ty": 218, "anchor": "start",
        "full_w": 193.44 + 403.2  # 596.64
    },

    # 2. C->>C: authenticate, run job_submit plugin, check limits and associations
    {
        "num": 2, "src": "C", "dst": "C", "y": 296,
        "circle": (490, 296),
        "arrow": ("self_right", 514, 545, 296, 324, 490),
        "card": (545, 280, 1010, 34, "#ffffff", "#207448"),
        "text_type": "inline",
        "text": [
            ("authenticate, run ", False),
            ("job_submit", True),
            (" plugin, check limits and associations", False)
        ],
        "tx": 565, "ty": 305, "anchor": "start",
        "full_w": 259.2 + 148.8 + 561.6  # 969.6
    },

    # 3. C-->>U: Submitted batch job 4217
    # 2 lines so it fits strictly between Lane U (180) and Lane C (490)!
    {
        "num": 3, "src": "C", "dst": "U", "y": 366,
        "circle": (490, 366),
        "arrow": ("reply_left", 466, 180, 366),
        "card": (200, 316, 255, 46, "#ffffff", "#207448"),
        "text_type": "multiline",
        "lines": [
            ("Submitted batch", False, 327.5, 335, "middle", 15 * 14.4),
            ("job 4217", False, 327.5, 355, "middle", 8 * 14.4)
        ]
    },

    # 4. C->>C: job PENDING in queue, scheduler loop and backfill evaluate it
    {
        "num": 4, "src": "C", "dst": "C", "y": 432,
        "circle": (490, 432),
        "arrow": ("self_right", 514, 545, 432, 460, 490),
        "card": (555, 416, 920, 34, "#ffffff", "#207448"),
        "text_type": "single",
        "text": "job PENDING in queue, scheduler loop and backfill evaluate it",
        "is_mono": False, "tx": 575, "ty": 441, "anchor": "start",
        "full_w": 61 * 14.4  # 878.4
    },

    # 5. C->>C: resources found: allocate nodes A and B, state RUNNING (ORANGE)
    {
        "num": 5, "src": "C", "dst": "C", "y": 498,
        "circle": (490, 498),
        "arrow": ("self_right_orange", 514, 545, 498, 526, 490),
        "card": (555, 482, 850, 34, "#ffffff", "#db8129"),
        "text_type": "single",
        "text": "resources found: allocate nodes A and B, state RUNNING",
        "is_mono": False, "tx": 575, "ty": 507, "anchor": "start",
        "full_w": 54 * 14.4,  # 777.6
        "orange": True
    },

    # 6. C->>D1: launch batch step (RPC tree fan-out)
    {
        "num": 6, "src": "C", "dst": "D1", "y": 564,
        "circle": (490, 564),
        "arrow": ("msg_right", 514, 1110, 564),
        "card": (525, 530, 570, 32, "#ffffff", "#207448"),
        "text_type": "single",
        "text": "launch batch step (RPC tree fan-out)",
        "is_mono": False, "tx": 810, "ty": 554, "anchor": "middle",
        "full_w": 36 * 14.4  # 518.4
    },

    # 7. C->>D2: prepare node (prolog)
    {
        "num": 7, "src": "C", "dst": "D2", "y": 630,
        "circle": (490, 630),
        "arrow": ("msg_right", 514, 1420, 630),
        "card": (525, 596, 360, 32, "#ffffff", "#207448"),
        "text_type": "single",
        "text": "prepare node (prolog)",
        "is_mono": False, "tx": 705, "ty": 620, "anchor": "middle",
        "full_w": 21 * 14.4  # 302.4
    },

    # 8. D1->>D1: prolog, fork slurmstepd, run the batch script
    {
        "num": 8, "src": "D1", "dst": "D1", "y": 696,
        "circle": (1110, 696),
        "arrow": ("self_left", 1086, 1055, 696, 724, 1110),
        "card": (335, 680, 705, 34, "#ffffff", "#207448"),
        "text_type": "inline",
        "text": [
            ("prolog, fork ", False),
            ("slurmstepd,", True),
            (" run the batch script", False)
        ],
        "tx": 355, "ty": 705, "anchor": "start",
        "full_w": 187.2 + 148.8 + 316.8  # 652.8
    },

    # 9. D1->>D2: script runs srun, steps launched on both nodes
    # Card sits to the left of D1 (370 to 1070), arrow leaves D1 (1134) to D2 (1420)!
    {
        "num": 9, "src": "D1", "dst": "D2", "y": 762,
        "circle": (1110, 762),
        "arrow": ("msg_right", 1134, 1420, 762),
        "card": (365, 746, 710, 32, "#ffffff", "#207448"),
        "text_type": "inline",
        "text": [
            ("script runs ", False),
            ("srun,", True),
            (" steps launched on both nodes", False)
        ],
        "tx": 385, "ty": 770, "anchor": "start",
        "full_w": 172.8 + 59.52 + 432.0  # 664.32
    },

    # 10. D1->>D1: epilog, cleanup of processes
    {
        "num": 10, "src": "D1", "dst": "D1", "y": 828,
        "circle": (1110, 828),
        "arrow": ("self_left", 1086, 1055, 828, 856, 1110),
        "card": (590, 812, 450, 34, "#ffffff", "#207448"),
        "text_type": "single",
        "text": "epilog, cleanup of processes",
        "is_mono": False, "tx": 815, "ty": 837, "anchor": "middle",
        "full_w": 28 * 14.4  # 403.2
    },

    # 11. D2->>D2: epilog, cleanup of processes
    {
        "num": 11, "src": "D2", "dst": "D2", "y": 894,
        "circle": (1420, 894),
        "arrow": ("self_left", 1396, 1365, 894, 922, 1420),
        "card": (900, 878, 450, 34, "#ffffff", "#207448"),
        "text_type": "single",
        "text": "epilog, cleanup of processes",
        "is_mono": False, "tx": 1125, "ty": 903, "anchor": "middle",
        "full_w": 28 * 14.4  # 403.2
    },

    # 12. D1->>C: job complete RPC
    {
        "num": 12, "src": "D1", "dst": "C", "y": 960,
        "circle": (1110, 960),
        "arrow": ("msg_left", 1086, 490, 960),
        "card": (650, 926, 280, 32, "#ffffff", "#207448"),
        "text_type": "single",
        "text": "job complete RPC",
        "is_mono": False, "tx": 790, "ty": 950, "anchor": "middle",
        "full_w": 16 * 14.4  # 230.4
    },

    # 13. C->>DBD: job record: times, resources, exit code, usage
    {
        "num": 13, "src": "C", "dst": "DBD", "y": 1026,
        "circle": (490, 1026),
        "arrow": ("msg_right", 514, 800, 1026),
        "card": (515, 992, 720, 32, "#ffffff", "#207448"),
        "text_type": "single",
        "text": "job record: times, resources, exit code, usage",
        "is_mono": False, "tx": 875, "ty": 1016, "anchor": "middle",
        "full_w": 46 * 14.4  # 662.4
    },

    # 14. C->>C: free nodes A and B, run scheduler again
    {
        "num": 14, "src": "C", "dst": "C", "y": 1092,
        "circle": (490, 1092),
        "arrow": ("self_right", 514, 545, 1092, 1120, 490),
        "card": (555, 1076, 610, 34, "#ffffff", "#207448"),
        "text_type": "single",
        "text": "free nodes A and B, run scheduler again",
        "is_mono": False, "tx": 575, "ty": 1101, "anchor": "start",
        "full_w": 39 * 14.4  # 561.6
    }
]

print("=== CHECKING REFINED STEPS PADDINGS ===")
for s in refined_steps:
    bx, by, bw, bh, fill, stroke = s["card"]
    assert bx >= 40, f"Step {s['num']}: bx={bx} < 40"
    assert bx + bw <= 1560, f"Step {s['num']}: right edge {bx+bw} > 1560"
    
    if s["text_type"] == "multiline":
        for line, is_mono, tx, ty, anchor, w in s["lines"]:
            if anchor == "middle":
                pad_l = (tx - w / 2.0) - bx
                pad_r = (bx + bw) - (tx + w / 2.0)
            print(f"Step {s['num']:2d} [line '{line}'] in box [{bx}..{bx+bw}]: pad_l={pad_l:.1f}px, pad_r={pad_r:.1f}px")
            assert pad_l >= 16.0 and pad_r >= 16.0
    else:
        full_w = s["full_w"]
        anchor = s["anchor"]
        tx = s["tx"]
        if anchor == "start":
            pad_l = tx - bx
            pad_r = (bx + bw) - (tx + full_w)
        elif anchor == "middle":
            pad_l = (tx - full_w / 2.0) - bx
            pad_r = (bx + bw) - (tx + full_w / 2.0)
        print(f"Step {s['num']:2d} in box [{bx:4d}..{bx+bw:4d}] (bw={bw:4d}): pad_l={pad_l:5.1f}px, pad_r={pad_r:5.1f}px | min={min(pad_l, pad_r):5.1f}px")
        assert pad_l >= 16.0 and pad_r >= 16.0

print("\nALL REFINED STEP PADDINGS >= 16px!")
