import xml.etree.ElementTree as ET
import re

def build_svg():
    W = 1600
    H = 1195
    
    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    lines.append('  <title>Reading hosts.ini: hosts, groups, groups of groups</title>')
    lines.append('  <desc>Visual infographic explaining hosts.ini structure, inventory nesting, group of groups with children, vars inheritance, and inspection commands.</desc>')
    lines.append('  <defs>')
    
    # Arrow marker green
    lines.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    lines.append('    </marker>')

    # Arrow marker orange
    lines.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    lines.append('    </marker>')

    # 56px Icons (stroke-width 4, green #207448)
    # Icon: Document / INI File
    lines.append('    <g id="icon-file" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <path d="M 10 4 L 34 4 L 46 16 L 46 52 L 10 52 Z" />')
    lines.append('      <polyline points="34,4 34,16 46,16" />')
    lines.append('      <line x1="18" y1="24" x2="38" y2="24" />')
    lines.append('      <line x1="18" y1="32" x2="38" y2="32" />')
    lines.append('      <line x1="18" y1="40" x2="30" y2="40" />')
    lines.append('    </g>')

    # Icon: Hierarchical Tree / Cluster
    lines.append('    <g id="icon-tree" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <rect x="20" y="6" width="16" height="12" rx="3" fill="#ffffff" />')
    lines.append('      <rect x="6" y="38" width="16" height="12" rx="3" fill="#ffffff" />')
    lines.append('      <rect x="34" y="38" width="16" height="12" rx="3" fill="#ffffff" />')
    lines.append('      <path d="M 28 18 L 28 28 L 14 28 L 14 38 M 28 28 L 42 28 L 42 38" />')
    lines.append('    </g>')

    # Icon: Server Host
    lines.append('    <g id="icon-server" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <rect x="6" y="8" width="44" height="18" rx="4" fill="#ffffff" />')
    lines.append('      <rect x="6" y="30" width="44" height="18" rx="4" fill="#ffffff" />')
    lines.append('      <circle cx="14" cy="17" r="2.5" fill="#207448" />')
    lines.append('      <circle cx="22" cy="17" r="2.5" fill="#207448" />')
    lines.append('      <line x1="32" y1="17" x2="42" y2="17" />')
    lines.append('      <circle cx="14" cy="39" r="2.5" fill="#207448" />')
    lines.append('      <circle cx="22" cy="39" r="2.5" fill="#207448" />')
    lines.append('      <line x1="32" y1="39" x2="42" y2="39" />')
    lines.append('    </g>')

    # Icon: Terminal Window
    lines.append('    <g id="icon-terminal" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <rect x="4" y="8" width="48" height="40" rx="6" fill="#ffffff" />')
    lines.append('      <line x1="4" y1="20" x2="52" y2="20" />')
    lines.append('      <circle cx="11" cy="14" r="2" fill="#207448" />')
    lines.append('      <circle cx="17" cy="14" r="2" fill="#207448" />')
    lines.append('      <path d="M 12 30 L 18 35 L 12 40" />')
    lines.append('      <line x1="22" y1="40" x2="34" y2="40" />')
    lines.append('    </g>')

    # Icon: Alert Triangle
    lines.append('    <g id="icon-alert" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <path d="M 28 6 L 50 46 L 6 46 Z" fill="#ffffff" />')
    lines.append('      <line x1="28" y1="20" x2="28" y2="32" />')
    lines.append('      <circle cx="28" cy="39" r="2" fill="#207448" />')
    lines.append('    </g>')

    # Icon: Phone Book / Directory
    lines.append('    <g id="icon-book" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('      <path d="M 8 10 C 16 6 28 6 28 14 L 28 48 C 28 40 16 40 8 44 Z" />')
    lines.append('      <path d="M 48 10 C 40 6 28 6 28 14 L 28 48 C 28 40 40 40 48 44 Z" />')
    lines.append('    </g>')

    lines.append('  </defs>')

    # Background
    lines.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')

    # Title (48px bold)
    lines.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Reading hosts.ini: hosts, groups, groups of groups</text>')

    # ================= LEFT CONTAINER: ANNOTATED INI FILE =================
    lines.append('  <g id="panel-ini">')
    lines.append('    <rect x="40" y="100" width="740" height="660" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    lines.append('    <use href="#icon-file" x="708" y="112" />')
    
    # 1. Section: [gpu]
    lines.append('    <rect x="60" y="116" width="630" height="124" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('    <text x="375" y="152" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="375" dy="0">[gpu]</tspan>')
    lines.append('      <tspan x="375" dy="32">gpu01 ansible_host=10.0.10.11,</tspan>')
    lines.append('      <tspan x="375" dy="32">gpu02 ansible_host=10.0.10.12</tspan>')
    lines.append('    </text>')

    # 2. Callout 2: a group collects hosts that share a role
    lines.append('    <rect x="60" y="250" width="700" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('    <text x="410" y="286" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">a group collects hosts that share a role</text>')

    # 3. Callout 1: each host has a name and optionally an address
    lines.append('    <rect x="60" y="316" width="700" height="90" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('    <text x="410" y="352" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="410" dy="0">each host has a name and</tspan>')
    lines.append('      <tspan x="410" dy="32">optionally an address</tspan>')
    lines.append('    </text>')

    # 4. Section: [login]
    lines.append('    <rect x="60" y="416" width="700" height="90" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('    <text x="410" y="452" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="410" dy="0">[login]</tspan>')
    lines.append('      <tspan x="410" dy="32">login01 ansible_host=10.0.10.5</tspan>')
    lines.append('    </text>')

    # 5. Section: [cluster:children]
    lines.append('    <rect x="60" y="516" width="700" height="90" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('    <text x="410" y="552" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="410" dy="0">[cluster:children]</tspan>')
    lines.append('      <tspan x="410" dy="32">gpu login</tspan>')
    lines.append('    </text>')

    # 6. Section: [cluster:vars]
    lines.append('    <rect x="60" y="616" width="700" height="124" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('    <text x="410" y="652" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="410" dy="0">[cluster:vars]</tspan>')
    lines.append('      <tspan x="410" dy="32">ansible_user=automation,</tspan>')
    lines.append('      <tspan x="410" dy="32">ansible_python_interpreter=/usr/bin/python3</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')

    # ================= RIGHT CONTAINER: TREE =================
    lines.append('  <g id="panel-tree">')
    lines.append('    <rect x="820" y="100" width="740" height="660" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    lines.append('    <use href="#icon-tree" x="1488" y="112" />')

    # Tree root: cluster
    lines.append('    <rect x="1050" y="130" width="280" height="70" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('    <text x="1190" y="175" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">cluster</text>')

    # Vars box attached to cluster
    lines.append('    <line x1="1190" y1="200" x2="1190" y2="240" stroke="#207448" stroke-width="2.5" stroke-dasharray="6,4" />')
    lines.append('    <rect x="910" y="240" width="560" height="90" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    lines.append('    <text x="1190" y="276" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="1190" dy="0">ansible_user and interpreter</tspan>')
    lines.append('      <tspan x="1190" dy="32">apply to all three machines</tspan>')
    lines.append('    </text>')

    # Branch connections from cluster down to gpu and login
    lines.append('    <path d="M 1190 330 L 1190 375 L 990 375 L 990 416" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
    lines.append('    <path d="M 1190 375 L 1390 375 L 1390 416" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')

    # Child 1: gpu
    lines.append('    <rect x="860" y="420" width="260" height="190" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('    <text x="990" y="468" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">gpu</text>')
    lines.append('    <use href="#icon-server" x="900" y="500" />')
    lines.append('    <use href="#icon-server" x="1024" y="500" />')

    # Child 2: login
    lines.append('    <rect x="1260" y="420" width="260" height="190" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('    <text x="1390" y="468" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">login</text>')
    lines.append('    <use href="#icon-server" x="1362" y="500" />')
    lines.append('  </g>')

    # ================= CALLOUT 3: GROUP OF GROUPS (ORANGE) =================
    lines.append('  <g id="callout-orange">')
    lines.append('    <rect x="40" y="780" width="1520" height="90" rx="14" fill="#fff9f5" stroke="#db8129" stroke-width="3" />')
    lines.append('    <text x="800" y="816" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    lines.append('      <tspan x="800" dy="0">a group of groups, written with :children, lets one command reach every</tspan>')
    lines.append('      <tspan x="800" dy="34">member: a play aimed at cluster reaches all three machines</tspan>')
    lines.append('    </text>')
    lines.append('  </g>')

    # ================= COMMANDS STRIP =================
    lines.append('  <g id="strip-commands">')
    lines.append('    <rect x="40" y="890" width="1520" height="75" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <use href="#icon-terminal" x="64" y="899" />')
    lines.append('    <text x="800" y="937" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">ansible-inventory --graph (run first: shows the nesting at a glance), --list, --host gpu01</text>')
    lines.append('  </g>')

    # ================= WARNING STRIP =================
    lines.append('  <g id="strip-warning">')
    lines.append('    <rect x="40" y="985" width="1520" height="75" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    lines.append('    <use href="#icon-alert" x="64" y="994" />')
    lines.append('    <text x="800" y="1031" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">a node missing from the inventory quietly misses every change you make</text>')
    lines.append('  </g>')

    # ================= BOTTOM BAR =================
    lines.append('  <g id="bottom-bar">')
    lines.append('    <rect x="40" y="1080" width="1520" height="75" rx="14" fill="#207448" />')
    lines.append('    <use href="#icon-book" x="64" y="1089" />')
    lines.append('    <text x="800" y="1127" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">The inventory is the phone book of your fleet</text>')
    lines.append('  </g>')

    lines.append('</svg>')
    return "\n".join(lines)

svg_text = build_svg()
with open("test_hosts_ini.svg", "w") as f:
    f.write(svg_text)
print("Saved test_hosts_ini.svg successfully.")
