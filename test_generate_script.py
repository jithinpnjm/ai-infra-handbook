import xml.etree.ElementTree as ET
import re, subprocess, os

def generate_svg():
    lines = []
    lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    lines.append('  <title>Top-down and bottom-up checklist</title>')
    lines.append('  <desc>Visual comparison checklist showing two vertical ladders side by side with a shared 8-rung list: top-down troubleshooting from application symptom to wire, and bottom-up hardware counter verification.</desc>')
    lines.append('  <defs>')
    lines.append('    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="8" markerHeight="8" orient="auto">')
    lines.append('      <path d="M 2 2 L 8 5 L 2 8 Z" fill="#207448" />')
    lines.append('    </marker>')
    lines.append('  </defs>')
    lines.append('')
    lines.append('  <!-- Background -->')
    lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    lines.append('')
    lines.append('  <!-- Main Title -->')
    lines.append('  <text x="800" y="65" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Top-down and bottom-up checklist</text>')
    lines.append('')

    # Layout coordinates:
    y_start = 168
    rung_h = 96
    gap = 18

    # Headers for the two ladders:
    lines.append('  <!-- Column Headers -->')
    lines.append('  <g id="ladder-headers">')
    # Left Ladder Header
    lines.append('    <rect x="50" y="100" width="940" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <text x="520" y="133" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">Top-down (application symptom to wire)</text>')
    lines.append('')
    # Right Ladder Header
    lines.append('    <rect x="1030" y="100" width="520" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <text x="1290" y="133" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#207448">Bottom-up goes the other way</text>')
    lines.append('  </g>')
    lines.append('')

    # Ladder Rails:
    rail_top = 158
    rail_bot = 1070
    rail_h = rail_bot - rail_top

    lines.append('  <!-- Vertical Ladder Rails -->')
    lines.append('  <g id="ladder-rails">')
    # Left Ladder Rails (Stiles)
    lines.append(f'    <rect x="58" y="{rail_top}" width="14" height="{rail_h}" rx="7" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append(f'    <rect x="968" y="{rail_top}" width="14" height="{rail_h}" rx="7" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Downward directional arrows on Left Ladder
    lines.append(f'    <line x1="65" y1="{rail_top + 12}" x2="65" y2="{rail_bot - 14}" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" stroke-dasharray="8 6" />')
    lines.append(f'    <line x1="975" y1="{rail_top + 12}" x2="975" y2="{rail_bot - 14}" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" stroke-dasharray="8 6" />')
    lines.append('')

    # Right Ladder Rails (Stiles)
    lines.append(f'    <rect x="1038" y="{rail_top}" width="14" height="{rail_h}" rx="7" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append(f'    <rect x="1538" y="{rail_top}" width="14" height="{rail_h}" rx="7" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Upward directional arrows on Right Ladder
    lines.append(f'    <line x1="1045" y1="{rail_bot - 12}" x2="1045" y2="{rail_top + 14}" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" stroke-dasharray="8 6" />')
    lines.append(f'    <line x1="1545" y1="{rail_bot - 12}" x2="1545" y2="{rail_top + 14}" stroke="#207448" stroke-width="4" marker-end="url(#arrow)" stroke-dasharray="8 6" />')
    lines.append('  </g>')
    lines.append('')

    # Shared Rung Horizontal Connectors:
    lines.append('  <!-- Shared Rung Bridges connecting the two ladders at each level -->')
    lines.append('  <g id="shared-rung-bridges">')
    for i in range(8):
        ry = y_start + i * (rung_h + gap) + rung_h // 2
        lines.append(f'    <line x1="982" y1="{ry}" x2="1038" y2="{ry}" stroke="#207448" stroke-width="6" stroke-linecap="round" />')
    lines.append('  </g>')
    lines.append('')

    left_steps = [
        {
            "num": 1,
            "title": "process listening",
            "pills": [("ss -tulpn", True)],
            "note": None
        },
        {
            "num": 2,
            "title": "connect test",
            "pills": [("nc -zv host port", True)],
            "note": "refusal versus timeout"
        },
        {
            "num": 3,
            "title": "DNS",
            "pills": [("getent hosts", True), ("dig", True)],
            "note": None
        },
        {
            "num": 4,
            "title": "route and source",
            "pills": [("ip route get &lt;dst&gt;", True), ("ip rule", True), ("rp_filter", True)],
            "note": None
        },
        {
            "num": 5,
            "title": "firewall",
            "pills": [("nft list ruleset", True), ("conntrack", True)],
            "note": None
        },
        {
            "num": 6,
            "title": "neighbours",
            "pills": [("ip neigh", True), ("arping", True)],
            "note": None
        },
        {
            "num": 7,
            "title": "interface",
            "pills": [("ip -s link", True), ("ethtool -S", True)],
            "note": None
        },
        {
            "num": 8,
            "title": "capture packets at both ends",
            "pills": [],
            "note": None
        }
    ]

    right_steps = {
        7: "link up",
        6: "speed and FEC",
        5: "errors",
        4: "ring buffers",
        3: "IRQ and CPU"
    }

    left_icons = [
        # 1: Process listening (terminal / process window)
        """<rect x="8" y="10" width="40" height="36" rx="4" fill="none" stroke="#207448" stroke-width="3.5" />
           <line x1="8" y1="20" x2="48" y2="20" stroke="#207448" stroke-width="2.5" />
           <polyline points="14,28 20,33 14,38" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
           <line x1="24" y1="38" x2="34" y2="38" stroke="#207448" stroke-width="3" stroke-linecap="round" />""",
        # 2: Connect test (handshake / socket link)
        """<circle cx="16" cy="28" r="8" fill="none" stroke="#207448" stroke-width="3.5" />
           <circle cx="40" cy="28" r="8" fill="none" stroke="#207448" stroke-width="3.5" />
           <line x1="24" y1="28" x2="32" y2="28" stroke="#207448" stroke-width="4" stroke-linecap="round" />
           <path d="M 12 16 A 16 16 0 0 1 44 16" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" />""",
        # 3: DNS (globe / network directory)
        """<circle cx="28" cy="28" r="19" fill="none" stroke="#207448" stroke-width="3.5" />
           <ellipse cx="28" cy="28" rx="9" ry="19" fill="none" stroke="#207448" stroke-width="2.5" />
           <line x1="9" y1="28" x2="47" y2="28" stroke="#207448" stroke-width="2.5" />""",
        # 4: Route and source (routing fork / signpost)
        """<circle cx="16" cy="38" r="5" fill="#207448" />
           <path d="M 21 38 C 28 38 32 30 38 20" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
           <polyline points="32,18 40,18 40,26" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
           <line x1="21" y1="38" x2="42" y2="38" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
           <polyline points="36,32 44,38 36,44" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />""",
        # 5: Firewall (shield)
        """<path d="M 28 8 L 46 15 V 28 C 46 39 28 47 28 47 C 28 47 10 39 10 28 V 15 Z" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" />
           <line x1="28" y1="16" x2="28" y2="38" stroke="#207448" stroke-width="3" stroke-linecap="round" />
           <line x1="18" y1="26" x2="38" y2="26" stroke="#207448" stroke-width="3" stroke-linecap="round" />""",
        # 6: Neighbours (linked hosts)
        """<rect x="8" y="16" width="15" height="24" rx="3" fill="none" stroke="#207448" stroke-width="3" />
           <rect x="33" y="16" width="15" height="24" rx="3" fill="none" stroke="#207448" stroke-width="3" />
           <line x1="23" y1="28" x2="33" y2="28" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
           <circle cx="15.5" cy="23" r="2" fill="#207448" />
           <circle cx="40.5" cy="23" r="2" fill="#207448" />""",
        # 7: Interface (Ethernet jack RJ-45)
        """<rect x="10" y="12" width="36" height="26" rx="4" fill="none" stroke="#207448" stroke-width="3.5" />
           <path d="M 20 38 V 44 H 36 V 38" fill="none" stroke="#207448" stroke-width="3" />
           <line x1="18" y1="18" x2="18" y2="24" stroke="#207448" stroke-width="2.5" />
           <line x1="24" y1="18" x2="24" y2="24" stroke="#207448" stroke-width="2.5" />
           <line x1="30" y1="18" x2="30" y2="24" stroke="#207448" stroke-width="2.5" />
           <line x1="36" y1="18" x2="36" y2="24" stroke="#207448" stroke-width="2.5" />""",
        # 8: Capture packets (magnifier over packet stream)
        """<rect x="8" y="14" width="24" height="20" rx="3" fill="none" stroke="#207448" stroke-width="3" />
           <circle cx="34" cy="32" r="10" fill="none" stroke="#207448" stroke-width="3.5" />
           <line x1="41" y1="39" x2="48" y2="46" stroke="#207448" stroke-width="4" stroke-linecap="round" />
           <line x1="14" y1="22" x2="26" y2="22" stroke="#207448" stroke-width="2" />"""
    ]

    right_icons = {
        7: """<line x1="10" y1="40" x2="46" y2="40" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
              <polyline points="18,24 28,12 38,24" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />
              <line x1="28" y1="12" x2="28" y2="34" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />""", # link up
        6: """<path d="M 10 38 A 20 20 0 1 1 46 38" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
              <circle cx="28" cy="28" r="4" fill="#207448" />
              <line x1="28" y1="28" x2="39" y2="18" stroke="#207448" stroke-width="3" stroke-linecap="round" />""", # speed and FEC
        5: """<polygon points="28,8 48,44 8,44" fill="none" stroke="#207448" stroke-width="3.5" stroke-linejoin="round" />
              <line x1="28" y1="20" x2="28" y2="30" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />
              <circle cx="28" cy="38" r="2.5" fill="#207448" />""", # errors
        4: """<circle cx="28" cy="28" r="18" fill="none" stroke="#207448" stroke-width="3" />
              <circle cx="28" cy="28" r="9" fill="none" stroke="#207448" stroke-width="2.5" />
              <line x1="28" y1="10" x2="28" y2="19" stroke="#207448" stroke-width="2.5" />
              <line x1="28" y1="37" x2="28" y2="46" stroke="#207448" stroke-width="2.5" />
              <line x1="10" y1="28" x2="19" y2="28" stroke="#207448" stroke-width="2.5" />
              <line x1="37" y1="28" x2="46" y2="28" stroke="#207448" stroke-width="2.5" />""", # ring buffers
        3: """<rect x="15" y="15" width="26" height="26" rx="4" fill="none" stroke="#207448" stroke-width="3" />
              <rect x="21" y="21" width="14" height="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
              <line x1="28" y1="8" x2="28" y2="15" stroke="#207448" stroke-width="2.5" />
              <line x1="28" y1="41" x2="28" y2="48" stroke="#207448" stroke-width="2.5" />
              <line x1="8" y1="28" x2="15" y2="28" stroke="#207448" stroke-width="2.5" />
              <line x1="41" y1="28" x2="48" y2="28" stroke="#207448" stroke-width="2.5" />""" # IRQ and CPU
    }

    # Render Left Ladder Rungs
    lines.append('  <!-- Left Ladder Rungs (Top-down) -->')
    lines.append('  <g id="top-down-rungs">')
    for i, s in enumerate(left_steps):
        ry = y_start + i * (rung_h + gap)
        lines.append(f'    <g id="td-rung-{s["num"]}">')
        lines.append(f'      <rect x="78" y="{ry}" width="884" height="{rung_h}" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
        # Number circle
        lines.append(f'      <circle cx="118" cy="{ry + 48}" r="22" fill="#207448" />')
        lines.append(f'      <text x="118" y="{ry + 56}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">{s["num"]}</text>')
        # Icon
        lines.append(f'      <g transform="translate(154, {ry + 20})">')
        lines.append(f'        {left_icons[i]}')
        lines.append('      </g>')
        
        if s["num"] == 1:
            lines.append(f'      <text x="230" y="{ry + 58}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">{s["title"]}</text>')
            lines.append(f'      <rect x="520" y="{ry + 26}" width="180" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="610" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][0][0]}</text>')
        elif s["num"] == 2:
            lines.append(f'      <text x="230" y="{ry + 42}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">{s["title"]}</text>')
            lines.append(f'      <rect x="440" y="{ry + 14}" width="280" height="40" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="580" y="{ry + 41}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][0][0]}</text>')
            lines.append(f'      <text x="230" y="{ry + 78}" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">{s["note"]}</text>')
        elif s["num"] == 3:
            lines.append(f'      <text x="230" y="{ry + 58}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">{s["title"]}</text>')
            lines.append(f'      <rect x="340" y="{ry + 26}" width="220" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="450" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][0][0]}</text>')
            lines.append(f'      <rect x="580" y="{ry + 26}" width="100" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="630" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][1][0]}</text>')
        elif s["num"] == 4:
            lines.append(f'      <text x="230" y="{ry + 40}" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#303a36">{s["title"]}</text>')
            lines.append(f'      <rect x="520" y="{ry + 14}" width="170" height="38" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="605" y="{ry + 40}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][2][0]}</text>')
            lines.append(f'      <rect x="230" y="{ry + 50}" width="320" height="38" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="390" y="{ry + 76}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][0][0]}</text>')
            lines.append(f'      <rect x="570" y="{ry + 50}" width="150" height="38" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="645" y="{ry + 76}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][1][0]}</text>')
        elif s["num"] == 5:
            lines.append(f'      <text x="230" y="{ry + 58}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">{s["title"]}</text>')
            lines.append(f'      <rect x="380" y="{ry + 26}" width="280" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="520" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][0][0]}</text>')
            lines.append(f'      <rect x="680" y="{ry + 26}" width="180" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="770" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][1][0]}</text>')
        elif s["num"] == 6:
            lines.append(f'      <text x="230" y="{ry + 58}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">{s["title"]}</text>')
            lines.append(f'      <rect x="440" y="{ry + 26}" width="190" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="535" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][0][0]}</text>')
            lines.append(f'      <rect x="650" y="{ry + 26}" width="150" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="725" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][1][0]}</text>')
        elif s["num"] == 7:
            lines.append(f'      <text x="230" y="{ry + 58}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">{s["title"]}</text>')
            lines.append(f'      <rect x="420" y="{ry + 26}" width="200" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="520" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][0][0]}</text>')
            lines.append(f'      <rect x="640" y="{ry + 26}" width="200" height="44" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
            lines.append(f'      <text x="740" y="{ry + 56}" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{s["pills"][1][0]}</text>')
        elif s["num"] == 8:
            lines.append(f'      <text x="230" y="{ry + 58}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">{s["title"]}</text>')
        lines.append('    </g>')
    lines.append('  </g>')
    lines.append('')

    # Render Right Ladder Rungs (Bottom-up)
    lines.append('  <!-- Right Ladder Rungs (Bottom-up) -->')
    lines.append('  <g id="bottom-up-rungs">')
    for i in range(8):
        ry = y_start + i * (rung_h + gap)
        lines.append(f'    <g id="bu-rung-{i+1}">')
        if i in right_steps:
            label = right_steps[i]
            lines.append(f'      <rect x="1060" y="{ry}" width="468" height="{rung_h}" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
            # Icon
            lines.append(f'      <g transform="translate(1085, {ry + 20})">')
            lines.append(f'        {right_icons[i]}')
            lines.append('      </g>')
            # Title
            lines.append(f'      <text x="1165" y="{ry + 58}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#303a36">{label}</text>')
        else:
            # Upper rungs 1, 2, 3: Open rungs showing continuation of bottom-up ladder to the top
            lines.append(f'      <rect x="1060" y="{ry}" width="468" height="{rung_h}" rx="12" fill="#f8faf8" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4" opacity="0.6" />')
            # Upward flow connector line
            lines.append(f'      <line x1="1294" y1="{ry + rung_h - 12}" x2="1294" y2="{ry + 16}" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" stroke-dasharray="6 4" opacity="0.7" />')
        lines.append('    </g>')
    lines.append('  </g>')
    lines.append('')

    # Orange Takeaway Bar at bottom:
    lines.append('  <!-- Orange Takeaway Bar -->')
    lines.append('  <g id="orange-takeaway-bar">')
    lines.append('    <rect x="50" y="1095" width="1500" height="70" rx="14" fill="#db8129" />')
    lines.append('    <text x="800" y="1139" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Application reports the failure: go top-down. Counters already rising: go bottom-up</text>')
    lines.append('  </g>')
    lines.append('</svg>')

    return '\n'.join(lines)

svg_str = generate_svg()
with open('test_candidate.svg', 'w') as f:
    f.write(svg_str)

print("Regenerated test_candidate.svg")
