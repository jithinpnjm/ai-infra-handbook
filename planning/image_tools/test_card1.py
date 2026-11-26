import re

# Test coordinates for horizontal 3-card layout
# Card dimensions: x=50, width=1500, height=270

# CARD 1:
# Title box: x=75, y=135, width=280, height=230
# Inside Title box: Icon at (x=100, y=160), Title at x=100, y=260
#
# Log lines box: x=380, y=135, width=540, height=230
# Inside Log lines box:
# Line 1: 'slurmctld: error: Nodes dgx-h100-14 not responding'
# Can it fit on 2 lines in 540 width?
# Available text width = 540 - 40 = 500 px.
# Monospace 24px: 14.88 px/char. Max chars in 500 px = 33 chars!
# 49 chars -> 2 lines:
# L1a: 'slurmctld: error: Nodes' (23c -> 342.2px)
# L1b: 'dgx-h100-14 not responding' (26c -> 386.9px)
# Both < 500px! Padding is (540 - 386.9) / 2 = 76.5px!
#
# Line 2: 'slurmctld: Node dgx-h100-14 now responding'
# L2a: 'slurmctld: Node' (15c -> 223.2px)
# L2b: 'dgx-h100-14 now responding' (26c -> 386.9px)
# Both < 500px!
#
# Cause box: x=945, y=135, width=580, height=105
# Text: 'rarely Slurm: packets dropped on the management network, or the node so loaded that slurmd cannot answer the ping in time'
# Sans 24px: 14.4 px/char. Available width = 580 - 40 = 540 px. Max chars = 37.5 -> 37 chars.
#
# Action box: x=945, y=250, width=580, height=115
# Text: 'investigate the network and node CPU and I/O load before touching Slurm settings; changing a timeout to hide a flapping node hides the fault'
# Max chars = 37 chars.

def wrap_text(text, max_chars):
    words = text.split()
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(" ".join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

print("=== CARD 1 CAUSE (width=580, max_chars=36) ===")
cause_lines = wrap_text("rarely Slurm: packets dropped on the management network, or the node so loaded that slurmd cannot answer the ping in time", 36)
for l in cause_lines:
    w = len(l) * 14.4
    print(f"  {len(l):2d}c: {w:5.1f}px (pad={(580-w)/2:.1f}px) '{l}'")

print("\n=== CARD 1 ACTION (width=580, max_chars=36) ===")
action_lines = wrap_text("investigate the network and node CPU and I/O load before touching Slurm settings; changing a timeout to hide a flapping node hides the fault", 36)
for l in action_lines:
    w = len(l) * 14.4
    print(f"  {len(l):2d}c: {w:5.1f}px (pad={(580-w)/2:.1f}px) '{l}'")
