#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def generate_svg():
    H = 1060
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>Multipath: one LUN, several paths</title>')
    svg.append('  <desc>Visual infographic explaining Linux multipath: SAN LUN with redundant paths merging into one multipathd device, LVM/filesystem layering, and rules.</desc>')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    
    # Title
    svg.append('  <text x="800" y="80" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Multipath: one LUN, several paths</text>')
    
    # ==================== UPPER SECTION: ARCHITECTURE FLOW ====================
    # Top y=140, Bottom y=575 (h=435)
    
    # --- COL 1: a SAN LUN ---
    # Box: x=50, y=140, w=270, h=435
    svg.append('  <!-- Left: a SAN LUN -->')
    svg.append('  <g id="san-lun">')
    svg.append('    <rect x="50" y="140" width="270" height="435" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Storage disk icon (56x56, centered at x=185, y=235)
    svg.append('    <g transform="translate(157, 235)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <ellipse cx="28" cy="14" rx="24" ry="9" />')
    svg.append('      <path d="M 4 14 V 30 C 4 35 15 39 28 39 C 41 39 52 35 52 30 V 14" />')
    svg.append('      <path d="M 4 30 V 46 C 4 51 15 55 28 55 C 41 55 52 51 52 46 V 30" />')
    svg.append('    </g>')
    # Label: a SAN LUN
    svg.append('    <text x="185" y="355" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">a SAN LUN</text>')
    svg.append('  </g>')
    
    # --- GAP 1: Arrow and edge label ---
    # Gap x=320..640 (w=320)
    # Arrow: from (320, 355) to (636, 355)
    # Edge label: "Two HBAs and two switches giving four paths" placed above the arrow
    svg.append('  <!-- Connection: SAN to OS -->')
    svg.append('  <line x1="320" y1="355" x2="636" y2="355" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    svg.append('  <text x="480" y="265" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="480" dy="0">Two HBAs and </tspan>')
    svg.append('    <tspan x="480" dy="32">two switches </tspan>')
    svg.append('    <tspan x="480" dy="32">giving four paths</tspan>')
    svg.append('  </text>')
    
    # --- COL 2: Middle: OS sees four block devices sdb, sdc, sdd, sde ---
    # Box: x=640, y=140, w=430, h=435
    svg.append('  <!-- Middle: OS block devices -->')
    svg.append('  <g id="middle-os-devices">')
    svg.append('    <rect x="640" y="140" width="430" height="435" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Host / CPU icon (56x56, centered at x=855, y=162)
    svg.append('    <g transform="translate(827, 162)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="8" width="40" height="40" rx="6" />')
    svg.append('      <line x1="16" y1="2" x2="16" y2="8" />')
    svg.append('      <line x1="28" y1="2" x2="28" y2="8" />')
    svg.append('      <line x1="40" y1="2" x2="40" y2="8" />')
    svg.append('      <line x1="16" y1="48" x2="16" y2="54" />')
    svg.append('      <line x1="28" y1="48" x2="28" y2="54" />')
    svg.append('      <line x1="40" y1="48" x2="40" y2="54" />')
    svg.append('      <line x1="2" y1="16" x2="8" y2="16" />')
    svg.append('      <line x1="2" y1="28" x2="8" y2="28" />')
    svg.append('      <line x1="2" y1="40" x2="8" y2="40" />')
    svg.append('      <line x1="48" y1="16" x2="54" y2="16" />')
    svg.append('      <line x1="48" y1="28" x2="54" y2="28" />')
    svg.append('      <line x1="48" y1="40" x2="54" y2="40" />')
    svg.append('    </g>')
    # Title label: OS sees four block devices sdb, sdc, sdd, sde
    svg.append('    <text x="855" y="254" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="855" dy="0">OS sees four </tspan>')
    svg.append('      <tspan x="855" dy="36">block devices </tspan>')
    svg.append('      <tspan x="855" dy="36">sdb, sdc, sdd, sde</tspan>')
    svg.append('    </text>')
    # Sub-card: (grey, component paths) -> styled grey!
    # Card x: 670..1040 (w=370), y: 400..535 (h=135)
    svg.append('    <rect x="670" y="400" width="370" height="135" rx="12" fill="#eef2f0" stroke="#8a9a94" stroke-width="2.5" />')
    svg.append('    <g transform="translate(827, 415)" stroke="#8a9a94" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 6 18 H 50" />')
    svg.append('      <path d="M 6 28 H 50" />')
    svg.append('      <path d="M 6 38 H 50" />')
    svg.append('    </g>')
    svg.append('    <text x="855" y="495" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#596561">component paths</text>')
    svg.append('  </g>')
    
    # --- GAP 2: Orange convergence arrow ---
    # From (1070, 465) to (1156, 465)
    # The single most important arrow: multipath merges 4 component paths into one device!
    svg.append('  <!-- Multipath merge arrow (single orange item) -->')
    svg.append('  <line x1="1070" y1="465" x2="1156" y2="465" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />')
    
    # --- COL 3: Right: multipathd device + LVM/filesystem on top ---
    # Stack container x=1160..1550 (w=390), y=140..575 (h=435)
    svg.append('  <!-- Right: device built by multipathd and LVM/FS on top -->')
    svg.append('  <g id="right-stack">')
    svg.append('    <rect x="1160" y="140" width="390" height="435" rx="16" fill="#f0f6f2" stroke="#207448" stroke-width="2.5" />')
    
    # Top box: then LVM and filesystem on top
    # x: 1180..1530 (w=350), y: 155..320 (h=165)
    svg.append('    <rect x="1180" y="155" width="350" height="165" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Window / FS icon (56x56, centered at x=1355, y=170)
    svg.append('    <g transform="translate(1327, 170)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="38" rx="4" />')
    svg.append('      <line x1="6" y1="20" x2="50" y2="20" />')
    svg.append('      <circle cx="14" cy="14" r="2" fill="#207448" />')
    svg.append('      <circle cx="22" cy="14" r="2" fill="#207448" />')
    svg.append('    </g>')
    svg.append('    <text x="1355" y="255" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="1355" dy="0">then LVM and </tspan>')
    svg.append('      <tspan x="1355" dy="36">filesystem on top</tspan>')
    svg.append('    </text>')
    
    # Arrow from bottom box up to top box: (1355, 375) to (1355, 324)
    svg.append('    <line x1="1355" y1="375" x2="1355" y2="324" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    
    # Bottom box: one device built by multipathd (green)
    # x: 1180..1530 (w=350), y: 375..550 (h=175)
    svg.append('    <rect x="1180" y="375" width="350" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Gear / service icon (56x56, centered at x=1355, y=388)
    svg.append('    <g transform="translate(1327, 388)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="14" />')
    svg.append('      <path d="M 28 6 V 14 M 28 42 V 50 M 6 28 H 14 M 42 28 H 50 M 12 12 L 18 18 M 38 38 L 44 44 M 12 44 L 18 38 M 38 18 L 44 12" />')
    svg.append('    </g>')
    svg.append('    <text x="1355" y="475" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    svg.append('      <tspan x="1355" dy="0">one device built </tspan>')
    svg.append('      <tspan x="1355" dy="36">by multipathd</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== LOWER SECTION: RULES & COMMAND ====================
    # Gap from y=575 to y=625 is 50 px >= 40 px
    # y: 625 to 1010 (h=385)
    
    # --- Rules List Panel ---
    # x: 50..1070 (w=1020), y: 625..1010 (h=385)
    svg.append('  <!-- Rules in a list -->')
    svg.append('  <g id="rules-list">')
    svg.append('    <rect x="50" y="625" width="1020" height="385" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    
    # Shield / check icon for rules
    svg.append('    <g transform="translate(75, 650)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 48 14 C 48 34 28 48 28 48 C 28 48 8 34 8 14 Z" />')
    svg.append('      <polyline points="20,26 26,32 36,20" />')
    svg.append('    </g>')
    
    # Rule 1
    svg.append('    <circle cx="150" cy="710" r="7" fill="#207448" />')
    svg.append('    <text x="175" y="705" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="175" dy="0">build filesystems and LVM on the multipath device, </tspan>')
    svg.append('      <tspan x="175" dy="34">never on a component path</tspan>')
    svg.append('    </text>')
    
    # Rule 2
    svg.append('    <circle cx="150" cy="820" r="7" fill="#207448" />')
    svg.append('    <text x="175" y="828" font-family="sans-serif" font-size="24" fill="#303a36">exclude paths in the LVM filter</text>')
    
    # Rule 3
    svg.append('    <circle cx="150" cy="920" r="7" fill="#207448" />')
    svg.append('    <text x="175" y="928" font-family="sans-serif" font-size="24" fill="#303a36">blacklist local disks and virtio disks</text>')
    svg.append('  </g>')
    
    # --- Command Box: multipath -ll ---
    # x: 1120..1550 (w=430), y: 625..1010 (h=385)
    # Monospace styled terminal box
    svg.append('  <!-- Monospace command -->')
    svg.append('  <g id="command-box">')
    svg.append('    <rect x="1120" y="625" width="430" height="385" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Terminal header bar
    svg.append('    <path d="M 1120 641 C 1120 632 1127 625 1136 625 H 1534 C 1543 625 1550 632 1550 641 V 675 H 1120 Z" fill="#e8f1ea" />')
    svg.append('    <circle cx="1145" cy="650" r="5" fill="#8a9a94" />')
    svg.append('    <circle cx="1162" cy="650" r="5" fill="#8a9a94" />')
    svg.append('    <circle cx="1179" cy="650" r="5" fill="#8a9a94" />')
    
    # Terminal icon (56x56, centered at x=1335, y=715)
    svg.append('    <g transform="translate(1307, 715)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polyline points="12,18 24,28 12,38" />')
    svg.append('      <line x1="28" y1="38" x2="44" y2="38" />')
    svg.append('    </g>')
    
    # Monospace text: multipath -ll
    svg.append('    <rect x="1160" y="810" width="350" height="85" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1335" y="862" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#207448">multipath -ll</text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return "\n".join(svg)

# Write to file
content = generate_svg()
with open("multipath.svg", "w", encoding="utf-8") as f:
    f.write(content)

print("Updated multipath.svg successfully.")
