#!/usr/bin/env python3
import re, subprocess, pathlib
import xml.etree.ElementTree as ET

# Participant definitions
# Width = 1600.
# Left margin = 50, right margin = 50.
# Available = 1500.
# 5 boxes of width 260: 1300.
# 4 gaps of 50: 200.
# Box 1: 50..310 (center 180)
# Box 2: 360..620 (center 490)
# Box 3: 670..930 (center 800)
# Box 4: 980..1240 (center 1110)
# Box 5: 1290..1550 (center 1420)

lanes = [
    {
        "id": "U",
        "title_lines": ["User on", "login node"],
        "bx": 50, "bw": 260, "cx": 180,
        "icon": "user"
    },
    {
        "id": "C",
        "title_lines": ["slurmctld"],
        "bx": 360, "bw": 260, "cx": 490,
        "icon": "gear"
    },
    {
        "id": "DBD",
        "title_lines": ["slurmdbd"],
        "bx": 670, "bw": 260, "cx": 800,
        "icon": "db"
    },
    {
        "id": "D1",
        "title_lines": ["slurmd on", "node A"],
        "bx": 980, "bw": 260, "cx": 1110,
        "icon": "chip"
    },
    {
        "id": "D2",
        "title_lines": ["slurmd on", "node B"],
        "bx": 1290, "bw": 260, "cx": 1420,
        "icon": "chip"
    }
]

# Let's inspect the steps
steps_data = [
    # 1. U->>C: sbatch job.sh (RPC with munge credential)
    {
        "num": 1, "src": "U", "dst": "C", "type": "msg",
        "card_w": 590, "card_h": 46,
        "lines": [("sbatch job.sh (RPC with munge credential)", False, 24)],
        # Wait, if card is 590 wide, let's see where it fits
    }
]

print("Participant lanes configured")
