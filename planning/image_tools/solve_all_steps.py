#!/usr/bin/env python3
import sys

# Participant centers
centers = {
    "U": 180,
    "C": 490,
    "DBD": 800,
    "D1": 1110,
    "D2": 1420
}

# 14 steps
# Let's define the layout of each step:
# Y coordinate: y_start = 230, delta = 66
# Each step has:
# - circle_cx, circle_cy, num
# - arrow type:
#     "msg_right": line from x1 to x2 at y, marker-end="url(#arrow-green)"
#     "msg_left": line from x1 to x2 at y, marker-end="url(#arrow-green-left)"
#     "reply_left": line from x1 to x2 at y, dashed, marker-end="url(#arrow-green-left)"
#     "self_right": loop from (cx+24, y) to (cx+45, y) to (cx+45, y+28) to (cx, y+28), marker-end="url(#arrow-green-left)"
#     "self_left": loop from (cx-24, y) to (cx-45, y) to (cx-45, y+28) to (cx, y+28), marker-end="url(#arrow-green)"
# - card: bx, by, bw, bh, fill, stroke
# - text lines: list of (line_text, is_mono, tx, ty, anchor)

# Let's verify conservative widths at 24px:
def est_w(text, is_mono=False):
    mult = 0.62 if is_mono else 0.6
    return len(text) * mult * 24

steps = [
    # 1. U->>C: sbatch job.sh (RPC with munge credential)
    {
        "num": 1,
        "src": "U", "dst": "C",
        "y": 230,
        "circle": (180, 230),
        "arrow": ("msg_right", 204, 490, 230, False),
        # Card sits above arrow line: y = 196, h = 32
        # Text: "sbatch job.sh (RPC with munge credential)"
        # sbatch job.sh is mono (13 chars * 14.88 = 193.44)
        #  (RPC with munge credential) is sans (28 chars * 14.4 = 403.2)
        # Total w = 596.6 px.
        # Card from x = 205 to 845 (w = 640).
        "card": (205, 196, 640, 32, "#ffffff", "#207448"),
        "text": [
            ("sbatch job.sh", True, 225, 220, "start"),
            (" (RPC with munge credential)", False, 225 + 193.44, 220, "start")
        ],
        "full_line": "sbatch job.sh (RPC with munge credential)",
        "full_w": 596.64
    },
    
    # 2. C->>C: authenticate, run job_submit plugin, check limits and associations
    {
        "num": 2,
        "src": "C", "dst": "C",
        "y": 296,
        "circle": (490, 296),
        "arrow": ("self_right", 514, 542, 296, 324, 490),
        # Card sits at x = 552 to 1530 (w = 978)
        # "authenticate, run job_submit plugin, check limits and associations"
        # "authenticate, run " (18 sans = 259.2)
        # "job_submit" (10 mono = 148.8)
        # " plugin, check limits and associations" (39 sans = 561.6)
        # Total w = 969.6 px.
        "card": (545, 280, 1010, 34, "#ffffff", "#207448"),
        "text": [
            ("authenticate, run ", False, 565, 305, "start"),
            ("job_submit", True, 565 + 259.2, 305, "start"),
            (" plugin, check limits and associations", False, 565 + 259.2 + 148.8, 305, "start")
        ],
        "full_line": "authenticate, run job_submit plugin, check limits and associations",
        "full_w": 969.6
    },

    # 3. C-->>U: Submitted batch job 4217
    {
        "num": 3,
        "src": "C", "dst": "U",
        "y": 362,
        "circle": (490, 362),
        "arrow": ("reply_left", 466, 180, 362, False),
        # Arrow goes from 466 to 180.
        # "Submitted batch job 4217" (24 sans * 14.4 = 345.6 px).
        # Card from x = 100 to 470 (w = 370).
        # Text centered at 285.
        "card": (85, 328, 385, 32, "#ffffff", "#207448"),
        "text": [
            ("Submitted batch job 4217", False, 277.5, 352, "middle")
        ],
        "full_line": "Submitted batch job 4217",
        "full_w": 345.6
    },

    # 4. C->>C: job PENDING in queue, scheduler loop and backfill evaluate it
    {
        "num": 4,
        "src": "C", "dst": "C",
        "y": 428,
        "circle": (490, 428),
        "arrow": ("self_right", 514, 542, 428, 456, 490),
        # 60 chars sans = 864 px.
        # Card from 550 to 1470 (w = 920).
        "card": (550, 412, 920, 34, "#ffffff", "#207448"),
        "text": [
            ("job PENDING in queue, scheduler loop and backfill evaluate it", False, 570, 437, "start")
        ],
        "full_line": "job PENDING in queue, scheduler loop and backfill evaluate it",
        "full_w": 878.4
    },

    # 5. C->>C: resources found: allocate nodes A and B, state RUNNING (ORANGE!)
    {
        "num": 5,
        "src": "C", "dst": "C",
        "y": 494,
        "circle": (490, 494),
        "arrow": ("self_right_orange", 514, 542, 494, 522, 490),
        # 55 chars sans = 792 px.
        # Card from 550 to 1400 (w = 850).
        "card": (550, 478, 850, 34, "#ffffff", "#db8129"),
        "text": [
            ("resources found: allocate nodes A and B, state RUNNING", False, 570, 503, "start")
        ],
        "full_line": "resources found: allocate nodes A and B, state RUNNING",
        "full_w": 792.0,
        "orange": True
    },

    # 6. C->>D1: launch batch step (RPC tree fan-out)
    {
        "num": 6,
        "src": "C", "dst": "D1",
        "y": 560,
        "circle": (490, 560),
        "arrow": ("msg_right", 514, 1110, 560, False),
        # Arrow from 514 to 1110.
        # 36 chars sans = 518.4 px.
        # Card sits above arrow from x = 525 to 1095 (w = 570).
        "card": (525, 526, 570, 32, "#ffffff", "#207448"),
        "text": [
            ("launch batch step (RPC tree fan-out)", False, 810, 550, "middle")
        ],
        "full_line": "launch batch step (RPC tree fan-out)",
        "full_w": 518.4
    },

    # 7. C->>D2: prepare node (prolog)
    {
        "num": 7,
        "src": "C", "dst": "D2",
        "y": 626,
        "circle": (490, 626),
        "arrow": ("msg_right", 514, 1420, 626, False),
        # Arrow from 514 to 1420.
        # 21 chars sans = 302.4 px.
        # Card from 525 to 885 (w = 360).
        "card": (525, 592, 360, 32, "#ffffff", "#207448"),
        "text": [
            ("prepare node (prolog)", False, 705, 616, "middle")
        ],
        "full_line": "prepare node (prolog)",
        "full_w": 302.4
    },

    # 8. D1->>D1: prolog, fork slurmstepd, run the batch script
    {
        "num": 8,
        "src": "D1", "dst": "D1",
        "y": 692,
        "circle": (1110, 692),
        "arrow": ("self_left", 1086, 1058, 692, 720, 1110),
        # Card sits to the LEFT of D1: from x = 360 to 1050 (w = 690)
        # "prolog, fork " (13 sans = 187.2)
        # "slurmstepd" (10 mono = 148.8)
        # ", run the batch script" (22 sans = 316.8)
        # Total w = 652.8 px.
        "card": (350, 676, 700, 34, "#ffffff", "#207448"),
        "text": [
            ("prolog, fork ", False, 370, 701, "start"),
            ("slurmstepd", True, 370 + 187.2, 701, "start"),
            (", run the batch script", False, 370 + 187.2 + 148.8, 701, "start")
        ],
        "full_line": "prolog, fork slurmstepd, run the batch script",
        "full_w": 652.8
    },

    # 9. D1->>D2: script runs srun, steps launched on both nodes
    {
        "num": 9,
        "src": "D1", "dst": "D2",
        "y": 758,
        "circle": (1110, 758),
        "arrow": ("msg_right", 1134, 1420, 758, False),
        # Arrow from 1134 to 1420.
        # "script runs " (12 sans = 172.8)
        # "srun" (4 mono = 59.52)
        # ", steps launched on both nodes" (30 sans = 432.0)
        # Total w = 664.32 px.
        # Card can extend to the left of D1: from x = 720 to 1410 (w = 690).
        "card": (720, 724, 700, 32, "#ffffff", "#207448"),
        "text": [
            ("script runs ", False, 738, 748, "start"),
            ("srun", True, 738 + 172.8, 748, "start"),
            (", steps launched on both nodes", False, 738 + 172.8 + 59.52, 748, "start")
        ],
        "full_line": "script runs srun, steps launched on both nodes",
        "full_w": 664.32
    },

    # 10. D1->>D1: epilog, cleanup of processes
    {
        "num": 10,
        "src": "D1", "dst": "D1",
        "y": 824,
        "circle": (1110, 824),
        "arrow": ("self_left", 1086, 1058, 824, 852, 1110),
        # 28 chars sans = 403.2 px.
        # Card sits to the LEFT of D1: from x = 600 to 1050 (w = 450).
        "card": (600, 808, 450, 34, "#ffffff", "#207448"),
        "text": [
            ("epilog, cleanup of processes", False, 825, 833, "middle")
        ],
        "full_line": "epilog, cleanup of processes",
        "full_w": 403.2
    },

    # 11. D2->>D2: epilog, cleanup of processes
    {
        "num": 11,
        "src": "D2", "dst": "D2",
        "y": 890,
        "circle": (1420, 890),
        "arrow": ("self_left", 1396, 1368, 890, 918, 1420),
        # 28 chars sans = 403.2 px.
        # Card sits to the LEFT of D2: from x = 910 to 1360 (w = 450).
        "card": (910, 874, 450, 34, "#ffffff", "#207448"),
        "text": [
            ("epilog, cleanup of processes", False, 1135, 899, "middle")
        ],
        "full_line": "epilog, cleanup of processes",
        "full_w": 403.2
    },

    # 12. D1->>C: job complete RPC
    {
        "num": 12,
        "src": "D1", "dst": "C",
        "y": 956,
        "circle": (1110, 956),
        "arrow": ("msg_left", 1086, 490, 956, False),
        # Arrow from 1086 to 490.
        # 16 chars sans = 230.4 px.
        # Card from 650 to 930 (w = 280).
        "card": (650, 922, 280, 32, "#ffffff", "#207448"),
        "text": [
            ("job complete RPC", False, 790, 946, "middle")
        ],
        "full_line": "job complete RPC",
        "full_w": 230.4
    },

    # 13. C->>DBD: job record: times, resources, exit code, usage
    {
        "num": 13,
        "src": "C", "dst": "DBD",
        "y": 1022,
        "circle": (490, 1022),
        "arrow": ("msg_right", 514, 800, 1022, False),
        # Arrow from 514 to 800.
        # 46 chars sans = 662.4 px.
        # Card from 515 to 1235 (w = 720).
        "card": (515, 988, 720, 32, "#ffffff", "#207448"),
        "text": [
            ("job record: times, resources, exit code, usage", False, 875, 1012, "middle")
        ],
        "full_line": "job record: times, resources, exit code, usage",
        "full_w": 662.4
    },

    # 14. C->>C: free nodes A and B, run scheduler again
    {
        "num": 14,
        "src": "C", "dst": "C",
        "y": 1088,
        "circle": (490, 1088),
        "arrow": ("self_right", 514, 542, 1088, 1116, 490),
        # 39 chars sans = 561.6 px.
        # Card from 550 to 1160 (w = 610).
        "card": (550, 1072, 610, 34, "#ffffff", "#207448"),
        "text": [
            ("free nodes A and B, run scheduler again", False, 570, 1097, "start")
        ],
        "full_line": "free nodes A and B, run scheduler again",
        "full_w": 561.6
    }
]

print("=== CHECKING ALL STEP PADDINGS ===")
for s in steps:
    bx, by, bw, bh, fill, stroke = s["card"]
    full_w = s["full_w"]
    # Check bounds inside 1600
    assert bx >= 40, f"Step {s['num']}: bx={bx} < 40"
    assert bx + bw <= 1560, f"Step {s['num']}: right edge {bx+bw} > 1560"
    
    # Check horizontal padding
    # If text is rendered from first start to last end:
    if s["text"][0][4] == "start":
        tx_start = s["text"][0][2]
        pad_l = tx_start - bx
        pad_r = (bx + bw) - (tx_start + full_w)
    elif s["text"][0][4] == "middle":
        tx_mid = s["text"][0][2]
        pad_l = (tx_mid - full_w / 2.0) - bx
        pad_r = (bx + bw) - (tx_mid + full_w / 2.0)
    
    print(f"Step {s['num']:2d} in box [{bx:4d}..{bx+bw:4d}] (bw={bw:4d}): pad_l={pad_l:5.1f}px, pad_r={pad_r:5.1f}px | min={min(pad_l, pad_r):5.1f}px")
    assert pad_l >= 16.0, f"Step {s['num']} pad_l={pad_l:.1f} < 16"
    assert pad_r >= 16.0, f"Step {s['num']} pad_r={pad_r:.1f} < 16"

print("ALL 14 STEP PADDINGS >= 16px!")
