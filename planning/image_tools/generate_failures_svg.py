import xml.etree.ElementTree as ET
import re
import pathlib

svg_path = "candidate_failures.svg"

# Let's define the exact content and line splits
title_text = "Eight early failures and where to look"

expected_labels = [
    "Eight early failures and where to look",
    "1 Invalid authentication credential or Unable to contact slurm controller: different munge keys, clock skew over a few minutes, munged not running, wrong permissions on /etc/munge or /run/munge",
    "2 Node invalid or drain with Low RealMemory: node line does not match what slurmd discovers; run slurmd -C",
    "3 Jobs rejected or sacctmgr hangs, Invalid account or account/partition combination: slurmdbd not running, wrong DB credentials, max_allowed_packet too small, blocked port, no association; follow the request: command to slurmdbd to database to login",
    "4 Controller will not start or empty queue: StateSaveLocation not writable, full, not shared, wiped",
    "5 Can't find an address, wrong user, Invalid user id: NodeName differs from hostname with no NodeHostname or NodeAddr, DNS or hosts inconsistencies, UID mismatch",
    "6 slurmd will not start after an OS upgrade: OS switched to cgroup v2 while Slurm built without v2, cgroup.conf forces v1, missing systemd delegation; stat -fc %T /sys/fs/cgroup",
    "7 Socket timed out on send/recv operation: polling loops from hundreds of clients running squeue every second, too small MaxJobCount, accounting back-pressure; run sdiag, look at RPC statistics by type and by user; use sacct for history, exporters that poll once, RPC rate limiting",
    "8 squeue and sinfo time out but running jobs continue: accounting database under strain, very wide sacct or sreport query; sdiag thread count and agent queue, slurmdbd.log lock waits, SHOW FULL PROCESSLIST in the database",
    "read the first error, not the last"
]

cards_def = [
    {
        "id": 1,
        "col": 0, "row": 0,
        "title": ["1 Invalid authentication credential", "or Unable to contact slurm", "controller:"],
        "body": [
            "different munge keys, clock skew over a",
            "few minutes, munged not running, wrong",
            "permissions on /etc/munge or /run/munge"
        ],
        "orange": True,
        "icon": "shield"
    },
    {
        "id": 2,
        "col": 1, "row": 0,
        "title": ["2 Node invalid or drain", "with Low RealMemory:"],
        "body": [
            "node line does not match what slurmd",
            "discovers; run slurmd -C"
        ],
        "orange": False,
        "icon": "ram"
    },
    {
        "id": 3,
        "col": 0, "row": 1,
        "title": ["3 Jobs rejected or sacctmgr hangs,", "Invalid account or", "account/partition combination:"],
        "body": [
            "slurmdbd not running, wrong DB credentials,",
            "max_allowed_packet too small, blocked port, no",
            "association; follow the request: command to",
            "slurmdbd to database to login"
        ],
        "orange": False,
        "icon": "db"
    },
    {
        "id": 4,
        "col": 1, "row": 1,
        "title": ["4 Controller will not start", "or empty queue:"],
        "body": [
            "StateSaveLocation not writable,",
            "full, not shared, wiped"
        ],
        "orange": False,
        "icon": "disk"
    },
    {
        "id": 5,
        "col": 0, "row": 2,
        "title": ["5 Can't find an address, wrong user,", "Invalid user id:"],
        "body": [
            "NodeName differs from hostname with no",
            "NodeHostname or NodeAddr, DNS or hosts",
            "inconsistencies, UID mismatch"
        ],
        "orange": False,
        "icon": "id"
    },
    {
        "id": 6,
        "col": 1, "row": 2,
        "title": ["6 slurmd will not start", "after an OS upgrade:"],
        "body": [
            "OS switched to cgroup v2 while Slurm built without",
            "v2, cgroup.conf forces v1, missing systemd",
            "delegation; stat -fc %T /sys/fs/cgroup"
        ],
        "orange": False,
        "icon": "gear"
    },
    {
        "id": 7,
        "col": 0, "row": 3,
        "title": ["7 Socket timed out on", "send/recv operation:"],
        "body": [
            "polling loops from hundreds of clients running",
            "squeue every second, too small MaxJobCount,",
            "accounting back-pressure; run sdiag, look at RPC",
            "statistics by type and by user; use sacct for",
            "history, exporters that poll once, RPC rate limiting"
        ],
        "orange": False,
        "icon": "clock"
    },
    {
        "id": 8,
        "col": 1, "row": 3,
        "title": ["8 squeue and sinfo time out", "but running jobs continue:"],
        "body": [
            "accounting database under strain, very wide sacct",
            "or sreport query; sdiag thread count and agent",
            "queue, slurmdbd.log lock waits,",
            "SHOW FULL PROCESSLIST in the database"
        ],
        "orange": False,
        "icon": "lockdb"
    }
]

# Coordinate planning:
# Width = 1600, Height = 1200
# Margins: left = 40, right = 40 -> total 1520
# Gap = 40
# Card width = 740
# Col 0: x = 40
# Col 1: x = 820

row_y = [85, 335, 595, 835]
row_h = [232, 242, 222, 252]

# Let's verify row spacing:
# Row 0: 85 .. 317 (h=232). Gap to Row 1 = 335 - 317 = 18 px
# Row 1: 335 .. 577 (h=242). Gap to Row 2 = 595 - 577 = 18 px
# Row 2: 595 .. 817 (h=222). Gap to Row 3 = 835 - 817 = 18 px
# Row 3: 835 .. 1087 (h=252). Gap to Takeaway = 1105 - 1087 = 18 px
# Takeaway: 1105 .. 1175 (h=70). Bottom margin = 1200 - 1175 = 25 px

lines = []
lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
lines.append('  <title>Eight early failures and where to look</title>')
lines.append('  <desc>A table of eight early Slurm failures with symptom, likely cause and the first diagnosis step.</desc>')
lines.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
lines.append('  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Eight early failures and where to look</text>')

icons_svg = {
    "shield": """<g transform="translate({ix}, {iy})" stroke="{stroke}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 22 4 L 38 10 V 22 C 38 31 22 38 22 38 C 22 38 6 31 6 22 V 10 Z"/>
        <circle cx="22" cy="18" r="3" fill="{stroke}"/>
        <line x1="22" y1="21" x2="22" y2="27"/>
      </g>""",
    "ram": """<g transform="translate({ix}, {iy})" stroke="{stroke}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="12" width="36" height="20" rx="3"/>
        <line x1="10" y1="32" x2="10" y2="38"/><line x1="16" y1="32" x2="16" y2="38"/><line x1="22" y1="32" x2="22" y2="38"/><line x1="28" y1="32" x2="28" y2="38"/><line x1="34" y1="32" x2="34" y2="38"/>
        <rect x="8" y="16" width="6" height="10" rx="1" fill="{stroke}"/>
        <rect x="18" y="16" width="6" height="10" rx="1" fill="{stroke}"/>
        <rect x="28" y="16" width="6" height="10" rx="1" fill="{stroke}"/>
      </g>""",
    "db": """<g transform="translate({ix}, {iy})" stroke="{stroke}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="22" cy="10" rx="16" ry="6"/>
        <path d="M 6 10 V 34 C 6 38 13 41 22 41 C 31 41 38 38 38 34 V 10"/>
        <path d="M 6 22 C 6 26 13 29 22 29 C 31 29 38 26 38 22"/>
      </g>""",
    "disk": """<g transform="translate({ix}, {iy})" stroke="{stroke}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="32" height="28" rx="4"/>
        <line x1="6" y1="26" x2="38" y2="26"/>
        <circle cx="31" cy="31" r="2" fill="{stroke}"/>
        <path d="M 12 18 L 18 18 L 22 14 L 32 14"/>
      </g>""",
    "id": """<g transform="translate({ix}, {iy})" stroke="{stroke}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="6" width="32" height="34" rx="4"/>
        <line x1="18" y1="6" x2="26" y2="6" stroke-width="4"/>
        <circle cx="22" cy="18" r="5"/>
        <path d="M 13 32 C 13 27 17 26 22 26 C 27 26 31 27 31 32"/>
      </g>""",
    "gear": """<g transform="translate({ix}, {iy})" stroke="{stroke}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="22" cy="22" r="7"/>
        <path d="M 22 5 L 22 10 M 22 34 L 22 39 M 5 22 L 10 22 M 34 22 L 39 22 M 10 10 L 14 14 M 30 30 L 34 34 M 10 34 L 14 30 M 30 14 L 34 10" stroke-width="3.5"/>
      </g>""",
    "clock": """<g transform="translate({ix}, {iy})" stroke="{stroke}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="22" cy="22" r="17"/>
        <polyline points="22,12 22,22 30,22"/>
        <line x1="22" y1="2" x2="22" y2="5"/>
      </g>""",
    "lockdb": """<g transform="translate({ix}, {iy})" stroke="{stroke}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <ellipse cx="22" cy="9" rx="14" ry="5"/>
        <path d="M 8 9 V 23 C 8 26 14 28 22 28 C 30 28 36 26 36 23 V 9"/>
        <rect x="17" y="24" width="16" height="13" rx="2" fill="#e8f1ea"/>
        <path d="M 21 24 V 20 C 21 17 29 17 29 20 V 24"/>
      </g>"""
}

for c in cards_def:
    cx = 40 if c["col"] == 0 else 820
    cy = row_y[c["row"]]
    ch = row_h[c["row"]]
    cw = 740
    
    # Border color: Card 1 is orange #db8129, others green #207448
    border_color = "#db8129" if c["orange"] else "#207448"
    border_w = "3.5" if c["orange"] else "2"
    
    lines.append(f'  <!-- Card {c["id"]} -->')
    lines.append(f'  <g id="card-{c["id"]}">')
    lines.append(f'    <rect x="{cx}" y="{cy}" width="{cw}" height="{ch}" rx="14" fill="#ffffff" stroke="{border_color}" stroke-width="{border_w}"/>')
    
    # Draw icon at top-left: cx + 18, cy + 18
    ix = cx + 18
    iy = cy + 18
    # Icon stroke is green #207448
    icon_code = icons_svg[c["icon"]].format(ix=ix, iy=iy, stroke="#207448")
    lines.append(f'    {icon_code}')
    
    # Text element:
    # Text starts at x = cx + 76
    # Y baseline 1 = cy + 40
    tx = cx + 76
    first_y = cy + 40
    
    lines.append(f'    <text x="{tx}" y="{first_y}" font-family="sans-serif" font-size="24" fill="#303a36">')
    
    # Title lines: 30px bold
    for i, tl in enumerate(c["title"]):
        if i == 0:
            lines.append(f'      <tspan x="{tx}" font-size="30" font-weight="bold" fill="#207448">{tl}</tspan>')
        else:
            lines.append(f'      <tspan x="{tx}" dy="35" font-size="30" font-weight="bold" fill="#207448">{tl}</tspan>')
            
    # Body lines: 24px regular
    for i, bl in enumerate(c["body"]):
        lines.append(f'      <tspan x="{tx}" dy="31" font-size="24" font-weight="normal" fill="#303a36">{bl}</tspan>')
        
    lines.append('    </text>')
    lines.append('  </g>')

# Takeaway bar at bottom
lines.append('  <!-- Takeaway bar -->')
lines.append('  <g id="takeaway-bar">')
lines.append('    <rect x="40" y="1105" width="1520" height="70" rx="14" fill="#207448"/>')
lines.append('    <text x="800" y="1149" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">read the first error, not the last</text>')
lines.append('  </g>')
lines.append('</svg>')

svg_content = '\n'.join(lines)
pathlib.Path(svg_path).write_text(svg_content)
print(f"Generated {svg_path} (length: {len(svg_content)} bytes)")
