#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

W = 1600
H = 1200

# We will generate the SVG string directly.
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
svg.append('  <title>From a failed unit message or status code to the layer that broke</title>')
svg.append('  <desc>Visual guide mapping systemctl and journal failure messages and systemd status codes to their root causes, with first-look commands and diagnostic workflow.</desc>')

# Defs
svg.append('  <defs>')
svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
svg.append('    </marker>')
svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
svg.append('    </marker>')
svg.append('  </defs>')

# Background
svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')

# Title (48px bold, centered)
svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">From a failed unit message or status code to the layer that broke</text>')

# ==============================================================================
# LEFT COLUMN: Message from systemctl or the journal
# ==============================================================================
col1_x = 40
col1_w = 730
col1_y = 95
col1_h = 875

# Left Column Container
svg.append(f'  <!-- Left Column Container -->')
svg.append(f'  <rect x="{col1_x}" y="{col1_y}" width="{col1_w}" height="{col1_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

# Left Column Header
svg.append(f'  <!-- Left Column Header -->')
# Icon for journal / systemctl messages (document with text lines, 56x56)
svg.append(f'  <g transform="translate(60, 105)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
svg.append('    <path d="M 8 4 L 36 4 L 48 16 L 48 52 L 8 52 Z" />')
svg.append('    <path d="M 36 4 L 36 16 L 48 16" stroke-width="3" />')
svg.append('    <line x1="16" y1="26" x2="40" y2="26" stroke-width="3.5" />')
svg.append('    <line x1="16" y1="34" x2="40" y2="34" stroke-width="3.5" />')
svg.append('    <line x1="16" y1="42" x2="28" y2="42" stroke-width="3.5" />')
svg.append('  </g>')
svg.append('  <text x="130" y="142" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Message from systemctl or the journal</text>')

# Left Column Cards (5 pairs)
# Left message box: x = 55, width = 325
# Arrow: x1 = 380, x2 = 410 (width 30)
# Left cause box: x = 410, width = 345
left_cards = [
    # 1
    {
        "y": 175, "h": 115,
        "msg": "Failed to start X: Unit X not found",
        "msg_lines": ["Failed to start X:", "Unit X not found"],
        "msg_mono": False,
        "cause": "wrong name, path or alias; daemon-reload may fix it",
        "cause_lines": ["wrong name, path or", "alias; daemon-reload", "may fix it"]
    },
    # 2
    {
        "y": 330, "h": 130,
        "msg": "Job for X failed because the control process exited with error code",
        "msg_lines": ["Job for X failed", "because the control", "process exited with", "error code"],
        "msg_mono": False,
        "cause": "read journalctl -xeu X",
        "cause_lines": ["read journalctl -xeu X"]
    },
    # 3
    {
        "y": 500, "h": 130,
        "msg": "start request repeated too quickly",
        "msg_lines": ["start request", "repeated too quickly"],
        "msg_mono": False,
        "cause": "start limit hit: reset-failed, fix the cause, lengthen RestartSec",
        "cause_lines": ["start limit hit:", "reset-failed, fix the", "cause, lengthen", "RestartSec"]
    },
    # 4
    {
        "y": 670, "h": 105,
        "msg": "Dependency failed for X",
        "msg_lines": ["Dependency failed", "for X"],
        "msg_mono": False,
        "cause": "a Requires dependency failed",
        "cause_lines": ["a Requires dependency", "failed"]
    },
    # 5
    {
        "y": 815, "h": 115,
        "msg": "Unit is masked",
        "msg_lines": ["Unit is masked"],
        "msg_mono": False,
        "cause": "the unit cannot be started at all",
        "cause_lines": ["the unit cannot be", "started at all"]
    }
]

for i, card in enumerate(left_cards, 1):
    cy = card["y"]
    ch = card["h"]
    mid_y = cy + ch / 2
    
    # Message box
    svg.append(f'  <!-- Left Card {i}: Message -->')
    svg.append(f'  <rect x="55" y="{cy}" width="325" height="{ch}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    
    # Text in message box
    n_lines = len(card["msg_lines"])
    start_y = mid_y - ((n_lines - 1) * 28) / 2 + 8
    svg.append(f'  <text x="217.5" y="{start_y}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    for idx, l in enumerate(card["msg_lines"]):
        dy = 0 if idx == 0 else 28
        svg.append(f'    <tspan x="217.5" dy="{dy}">{l}</tspan>')
    svg.append('  </text>')
    
    # Arrow from Message to Cause
    svg.append(f'  <!-- Left Card {i}: Arrow -->')
    svg.append(f'  <line x1="380" y1="{mid_y}" x2="408" y2="{mid_y}" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    
    # Cause box
    svg.append(f'  <!-- Left Card {i}: Cause -->')
    svg.append(f'  <rect x="410" y="{cy}" width="345" height="{ch}" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    
    # Text in cause box
    c_lines = len(card["cause_lines"])
    c_start_y = mid_y - ((c_lines - 1) * 28) / 2 + 8
    svg.append(f'  <text x="582.5" y="{c_start_y}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    for idx, l in enumerate(card["cause_lines"]):
        dy = 0 if idx == 0 else 28
        svg.append(f'    <tspan x="582.5" dy="{dy}">{l}</tspan>')
    svg.append('  </text>')


# ==============================================================================
# RIGHT COLUMN: status= code
# ==============================================================================
col2_x = 810
col2_w = 750
col2_y = 95
col2_h = 875

# Right Column Container
svg.append(f'  <!-- Right Column Container -->')
svg.append(f'  <rect x="{col2_x}" y="{col2_y}" width="{col2_w}" height="{col2_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

# Right Column Header
svg.append(f'  <!-- Right Column Header -->')
# Icon for systemd status codes (gear icon with status mark, 56x56)
svg.append(f'  <g transform="translate(830, 105)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
svg.append('    <circle cx="28" cy="28" r="12" />')
svg.append('    <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12.5 12.5 L 16.7 16.7 M 39.3 39.3 L 43.5 43.5 M 12.5 43.5 L 16.7 39.3 M 39.3 16.7 L 43.5 12.5" />')
svg.append('  </g>')
svg.append('  <text x="910" y="142" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">status= code</text>')

# Right Column Cards (7 pairs)
# Right code box: x = 825, width = 255
# Arrow: x1 = 1080, x2 = 1108 (width 30)
# Right cause box: x = 1110, width = 435
right_cards = [
    # 1: 203/EXEC (orange)
    {
        "y": 175, "h": 130,
        "is_orange": True,
        "code": "203/EXEC",
        "code_lines": ["203/EXEC"],
        "cause": "ExecStart binary cannot run: path, permissions, a noexec mount, wrong architecture, or a bad shebang",
        "cause_lines": [
            "ExecStart binary cannot run:",
            "path, permissions, a noexec",
            "mount, wrong architecture,",
            "or a bad shebang"
        ]
    },
    # 2: 200/CHDIR
    {
        "y": 320, "h": 75,
        "is_orange": False,
        "code": "200/CHDIR",
        "code_lines": ["200/CHDIR"],
        "cause": "bad WorkingDirectory=",
        "cause_lines": ["bad WorkingDirectory="]
    },
    # 3: 217/USER
    {
        "y": 410, "h": 75,
        "is_orange": False,
        "code": "217/USER",
        "code_lines": ["217/USER"],
        "cause": "bad User=",
        "cause_lines": ["bad User="]
    },
    # 4: 226/NAMESPACE
    {
        "y": 500, "h": 75,
        "is_orange": False,
        "code": "226/NAMESPACE",
        "code_lines": ["226/NAMESPACE"],
        "cause": "sandbox mount problem",
        "cause_lines": ["sandbox mount problem"]
    },
    # 5: 1/FAILURE
    {
        "y": 590, "h": 75,
        "is_orange": False,
        "code": "1/FAILURE",
        "code_lines": ["1/FAILURE"],
        "cause": "the program's own exit",
        "cause_lines": ["the program's own exit"]
    },
    # 6: signal=KILL or code=killed
    {
        "y": 680, "h": 95,
        "is_orange": False,
        "code": "signal=KILL or code=killed",
        "code_lines": ["signal=KILL or", "code=killed"],
        "cause": "killed by the OOM killer or a timeout",
        "cause_lines": ["killed by the OOM killer", "or a timeout"]
    },
    # 7: Result: timeout
    {
        "y": 790, "h": 75,
        "is_orange": False,
        "code": "Result: timeout",
        "code_lines": ["Result: timeout"],
        "cause": "unit ran past its time limit",
        "cause_lines": ["unit ran past its time limit"]
    }
]

for i, card in enumerate(right_cards, 1):
    cy = card["y"]
    ch = card["h"]
    mid_y = cy + ch / 2
    is_orange = card["is_orange"]
    
    stroke_col = "#db8129" if is_orange else "#207448"
    stroke_w = "3" if is_orange else "2"
    marker_url = "url(#arrow-orange)" if is_orange else "url(#arrow-green)"
    text_col = "#db8129" if is_orange else "#303a36"
    
    # Code box
    svg.append(f'  <!-- Right Card {i}: Code -->')
    svg.append(f'  <rect x="825" y="{cy}" width="255" height="{ch}" rx="10" fill="#ffffff" stroke="{stroke_col}" stroke-width="{stroke_w}" />')
    
    # Text in code box
    n_lines = len(card["code_lines"])
    start_y = mid_y - ((n_lines - 1) * 28) / 2 + 8
    font_weight = ' font-weight="bold"' if is_orange else ''
    svg.append(f'  <text x="952.5" y="{start_y}" text-anchor="middle" font-family="monospace" font-size="24"{font_weight} fill="{text_col}">')
    for idx, l in enumerate(card["code_lines"]):
        dy = 0 if idx == 0 else 28
        svg.append(f'    <tspan x="952.5" dy="{dy}">{l}</tspan>')
    svg.append('  </text>')
    
    # Arrow from Code to Cause
    svg.append(f'  <!-- Right Card {i}: Arrow -->')
    svg.append(f'  <line x1="1080" y1="{mid_y}" x2="1108" y2="{mid_y}" stroke="{stroke_col}" stroke-width="3.5" marker-end="{marker_url}" />')
    
    # Cause box
    svg.append(f'  <!-- Right Card {i}: Cause -->')
    svg.append(f'  <rect x="1110" y="{cy}" width="435" height="{ch}" rx="10" fill="#ffffff" stroke="{stroke_col}" stroke-width="{stroke_w}" />')
    
    # Text in cause box
    c_lines = len(card["cause_lines"])
    c_start_y = mid_y - ((c_lines - 1) * 28) / 2 + 8
    svg.append(f'  <text x="1327.5" y="{c_start_y}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    for idx, l in enumerate(card["cause_lines"]):
        dy = 0 if idx == 0 else 28
        svg.append(f'    <tspan x="1327.5" dy="{dy}">{l}</tspan>')
    svg.append('  </text>')


# ==============================================================================
# BOTTOM STRIP: First-look commands
# ==============================================================================
strip_x = 40
strip_w = 1520
strip_y = 1010
strip_h = 65

svg.append(f'  <!-- Bottom Strip: First-look Commands -->')
svg.append(f'  <rect x="{strip_x}" y="{strip_y}" width="{strip_w}" height="{strip_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

# Command boxes inside the strip:
# 1: 'systemctl status' (w=290)
# 2: 'journalctl -u NAME -b' (w=360)
# 3: 'systemctl cat' (w=250)
# 4: 'systemd-analyze verify FILE' (w=460)
cmd_boxes = [
    (65, 290, "systemctl status"),
    (385, 360, "journalctl -u NAME -b"),
    (775, 250, "systemctl cat"),
    (1055, 480, "systemd-analyze verify FILE")
]

for bx, bw, cmd in cmd_boxes:
    svg.append(f'  <rect x="{bx}" y="1018" width="{bw}" height="49" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    cx = bx + bw / 2
    svg.append(f'  <text x="{cx}" y="1051" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">{cmd}</text>')


# ==============================================================================
# BOTTOM TAKEAWAY BAR
# ==============================================================================
bar_x = 40
bar_w = 1520
bar_y = 1115
bar_h = 45

svg.append(f'  <!-- Bottom Bar: Takeaway -->')
svg.append(f'  <rect x="{bar_x}" y="{bar_y}" width="{bar_w}" height="{bar_h}" rx="10" fill="#207448" />')
svg.append(f'  <text x="800" y="1147" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Start with the status code, then read the journal for that unit</text>')

svg.append('</svg>')

result_svg = "\n".join(svg)

with open("status_ladder.svg", "w") as f:
    f.write(result_svg)

print("Generated status_ladder.svg successfully!")
