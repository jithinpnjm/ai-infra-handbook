#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

# Let's write the comprehensive generator and validator
def generate_svg():
    W = 1600
    H = 1150
    BG = "#f5f8f5"
    TEXT = "#303a36"
    GREEN = "#207448"
    PANEL_BG = "#e8f1ea"
    ORANGE = "#db8129"
    WHITE = "#ffffff"

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>ssh_config: the first matching Host block wins for each setting</title>')
    svg.append('  <desc>Visual infographic explaining how ssh_config evaluates settings from matching Host blocks in order, where the first match wins.</desc>')
    svg.append('  <defs>')
    
    # Markers (about 18px proportional)
    # Green arrow marker
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    
    # Orange arrow marker
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')

    # Slate / grey arrow marker for Card 3
    svg.append('    <marker id="arrow-slate" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#303a36" />')
    svg.append('    </marker>')

    # Icons (56x56 px, stroke-width 4, green stroke #207448)
    # Icon 1: Server / GPU Host icon
    svg.append('    <g id="icon-server" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="8" width="48" height="18" rx="4" fill="#ffffff" />')
    svg.append('      <rect x="4" y="30" width="48" height="18" rx="4" fill="#ffffff" />')
    svg.append('      <circle cx="12" cy="17" r="3" fill="#207448" />')
    svg.append('      <circle cx="20" cy="17" r="3" fill="#207448" />')
    svg.append('      <line x1="32" y1="17" x2="44" y2="17" />')
    svg.append('      <circle cx="12" cy="39" r="3" fill="#207448" />')
    svg.append('      <circle cx="20" cy="39" r="3" fill="#207448" />')
    svg.append('      <line x1="32" y1="39" x2="44" y2="39" />')
    svg.append('    </g>')

    # Icon 2: Pattern / Cluster Gateway icon (cards / wildcards)
    svg.append('    <g id="icon-pattern" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="10" width="32" height="38" rx="4" fill="#ffffff" />')
    svg.append('      <path d="M 18 6 L 46 6 C 48.2 6 50 7.8 50 10 L 50 38" />')
    svg.append('      <line x1="14" y1="20" x2="30" y2="20" />')
    svg.append('      <line x1="14" y1="28" x2="26" y2="28" />')
    svg.append('      <line x1="14" y1="36" x2="30" y2="36" />')
    svg.append('    </g>')

    # Icon 3: Wildcard / Global Host icon
    svg.append('    <g id="icon-global" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="22" fill="#ffffff" />')
    svg.append('      <ellipse cx="28" cy="28" rx="10" ry="22" />')
    svg.append('      <line x1="6" y1="28" x2="50" y2="28" />')
    svg.append('    </g>')

    # Icon 4: Terminal Window / Execution panel icon
    svg.append('    <g id="icon-terminal" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="48" height="44" rx="6" fill="#ffffff" />')
    svg.append('      <line x1="4" y1="18" x2="52" y2="18" />')
    svg.append('      <circle cx="11" cy="12" r="2" fill="#207448" />')
    svg.append('      <circle cx="17" cy="12" r="2" fill="#207448" />')
    svg.append('      <path d="M 12 28 L 18 34 L 12 40" />')
    svg.append('      <line x1="24" y1="40" x2="36" y2="40" />')
    svg.append('    </g>')

    # Icon 5: Key / Takeaway icon
    svg.append('    <g id="icon-key" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="18" cy="28" r="12" fill="#ffffff" />')
    svg.append('      <circle cx="18" cy="28" r="5" fill="#207448" />')
    svg.append('      <line x1="30" y1="28" x2="52" y2="28" />')
    svg.append('      <line x1="44" y1="28" x2="44" y2="36" />')
    svg.append('      <line x1="50" y1="28" x2="50" y2="34" />')
    svg.append('    </g>')

    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="{BG}" />')

    # Title (48px bold, wrapped onto 2 lines with tspan to never overflow)
    # Total text: "ssh_config: the first matching Host block wins for each setting"
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">ssh_config: the first matching Host block </tspan>')
    svg.append('    <tspan x="800" dy="56">wins for each setting</tspan>')
    svg.append('  </text>')

    # ================= LEFT COLUMN: CONFIG BLOCKS =================
    # Card 1: 'Host gpu01' with 'HostName 10.20.0.11' and 'User alice'
    svg.append('  <g id="card-1">')
    svg.append('    <rect x="50" y="165" width="470" height="240" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="95" cy="205" r="24" fill="#207448" />')
    svg.append('    <text x="95" y="214" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>')
    svg.append('    <text x="135" y="215" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Host gpu01</text>')
    svg.append('    <use href="#icon-server" x="444" y="177" />')
    # Row 1: HostName 10.20.0.11
    svg.append('    <rect x="75" y="250" width="420" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="95" y="285" font-family="monospace" font-size="24" fill="#303a36">HostName 10.20.0.11</text>')
    # Row 2: User alice
    svg.append('    <rect x="75" y="320" width="420" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="95" y="355" font-family="monospace" font-size="24" fill="#303a36">User alice</text>')
    svg.append('  </g>')

    # Card 2: 'Host gpu* login*' with 'User clusterdefault' and 'ProxyJump bastion'
    svg.append('  <g id="card-2">')
    svg.append('    <rect x="50" y="450" width="470" height="240" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="95" cy="490" r="24" fill="#207448" />')
    svg.append('    <text x="95" y="499" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>')
    svg.append('    <text x="135" y="500" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Host gpu* login*</text>')
    svg.append('    <use href="#icon-pattern" x="444" y="462" />')
    # Row 1: User clusterdefault
    svg.append('    <rect x="75" y="535" width="420" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="95" y="570" font-family="monospace" font-size="24" fill="#303a36">User clusterdefault</text>')
    # Row 2: ProxyJump bastion
    svg.append('    <rect x="75" y="605" width="420" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="95" y="640" font-family="monospace" font-size="24" fill="#303a36">ProxyJump bastion</text>')
    svg.append('  </g>')

    # Card 3: 'Host *' with 'ServerAliveInterval 30' and 'User fallback'
    svg.append('  <g id="card-3">')
    svg.append('    <rect x="50" y="735" width="470" height="240" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="95" cy="775" r="24" fill="#207448" />')
    svg.append('    <text x="95" y="784" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>')
    svg.append('    <text x="135" y="785" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Host *</text>')
    svg.append('    <use href="#icon-global" x="444" y="747" />')
    # Row 1: ServerAliveInterval 30
    svg.append('    <rect x="75" y="820" width="420" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="95" y="855" font-family="monospace" font-size="24" fill="#303a36">ServerAliveInterval 30</text>')
    # Row 2: User fallback
    svg.append('    <rect x="75" y="890" width="420" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="95" y="925" font-family="monospace" font-size="24" fill="#303a36">User fallback</text>')
    svg.append('  </g>')

    # ================= RIGHT COLUMN: RESULT PANELS =================
    # Panel 1: 'ssh gpu01 matches cards 1, 2, 3'
    svg.append('  <g id="panel-1">')
    svg.append('    <rect x="770" y="165" width="780" height="385" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-terminal" x="795" y="177" />')
    svg.append('    <text x="865" y="215" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">ssh gpu01 matches cards 1, 2, 3</text>')
    
    # Table rows in Panel 1
    # Row 1: HostName 10.20.0.11 (from card 1)
    svg.append('    <rect x="795" y="250" width="730" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="815" y="285" font-family="sans-serif" font-size="24" fill="#303a36">HostName 10.20.0.11 (from card 1)</text>')
    
    # Row 2: User alice (card 1 wins over cards 2 and 3) -> ORANGE OUTLINE
    svg.append('    <rect x="795" y="320" width="730" height="54" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    svg.append('    <text x="815" y="355" font-family="sans-serif" font-size="24" fill="#303a36">User alice (card 1 wins over cards 2 and 3)</text>')
    
    # Row 3: ProxyJump bastion (card 2)
    svg.append('    <rect x="795" y="390" width="730" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="815" y="425" font-family="sans-serif" font-size="24" fill="#303a36">ProxyJump bastion (card 2)</text>')
    
    # Row 4: ServerAliveInterval 30 (card 3)
    svg.append('    <rect x="795" y="460" width="730" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="815" y="495" font-family="sans-serif" font-size="24" fill="#303a36">ServerAliveInterval 30 (card 3)</text>')
    svg.append('  </g>')

    # Panel 2: 'ssh gpu02 matches cards 2, 3'
    svg.append('  <g id="panel-2">')
    svg.append('    <rect x="770" y="590" width="780" height="385" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-terminal" x="795" y="602" />')
    svg.append('    <text x="865" y="640" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">ssh gpu02 matches cards 2, 3</text>')
    
    # Table rows in Panel 2
    # Row 1: HostName gpu02 (no card sets it)
    svg.append('    <rect x="795" y="675" width="730" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="815" y="710" font-family="sans-serif" font-size="24" fill="#303a36">HostName gpu02 (no card sets it)</text>')
    
    # Row 2: User clusterdefault (card 2)
    svg.append('    <rect x="795" y="745" width="730" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="815" y="780" font-family="sans-serif" font-size="24" fill="#303a36">User clusterdefault (card 2)</text>')
    
    # Row 3: ProxyJump bastion (card 2)
    svg.append('    <rect x="795" y="815" width="730" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="815" y="850" font-family="sans-serif" font-size="24" fill="#303a36">ProxyJump bastion (card 2)</text>')
    
    # Row 4: ServerAliveInterval 30 (card 3)
    svg.append('    <rect x="795" y="885" width="730" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="815" y="920" font-family="sans-serif" font-size="24" fill="#303a36">ServerAliveInterval 30 (card 3)</text>')
    svg.append('  </g>')

    # ================= ARROWS =================
    # Exactly 7 arrows:
    # From each value to the card that supplied it, colour-coded by card, never crossing text.
    # Card 1 supplies: HostName 10.20.0.11 (Panel 1), User alice (Panel 1)
    # Card 2 supplies: ProxyJump bastion (Panel 1), User clusterdefault (Panel 2), ProxyJump bastion (Panel 2)
    # Card 3 supplies: ServerAliveInterval 30 (Panel 1), ServerAliveInterval 30 (Panel 2)

    # 1. From Panel 1 Row 1 HostName to Card 1
    # Directly horizontal at y = 277
    svg.append('  <path d="M 795 277 L 522 277" stroke="#207448" stroke-width="3" fill="none" marker-end="url(#arrow-green)" />')

    # 2. From Panel 1 Row 2 User alice to Card 1 (ORANGE ARROW for winning value)
    # Directly horizontal at y = 347
    svg.append('  <path d="M 795 347 L 522 347" stroke="#db8129" stroke-width="3.5" fill="none" marker-end="url(#arrow-orange)" />')

    # 3. From Panel 1 Row 3 ProxyJump bastion to Card 2
    # Lands at upper part of ProxyJump bastion in Card 2 (y = 620)
    svg.append('  <path d="M 795 417 C 650 417, 650 620, 522 620" stroke="#207448" stroke-width="3" fill="none" marker-end="url(#arrow-green)" />')

    # 4. From Panel 1 Row 4 ServerAliveInterval 30 to Card 3
    # Lands at upper part of ServerAliveInterval 30 in Card 3 (y = 835)
    svg.append('  <path d="M 795 487 C 610 487, 610 835, 522 835" stroke="#303a36" stroke-width="3" fill="none" marker-end="url(#arrow-slate)" />')

    # 5. From Panel 2 Row 2 User clusterdefault to Card 2
    # Lands at User clusterdefault in Card 2 (y = 562)
    svg.append('  <path d="M 795 772 C 670 772, 670 562, 522 562" stroke="#207448" stroke-width="3" fill="none" marker-end="url(#arrow-green)" />')

    # 6. From Panel 2 Row 3 ProxyJump bastion to Card 2
    # Lands at lower part of ProxyJump bastion in Card 2 (y = 644)
    svg.append('  <path d="M 795 842 C 685 842, 685 644, 522 644" stroke="#207448" stroke-width="3" fill="none" marker-end="url(#arrow-green)" />')

    # 7. From Panel 2 Row 4 ServerAliveInterval 30 to Card 3
    # Lands at lower part of ServerAliveInterval 30 in Card 3 (y = 859)
    svg.append('  <path d="M 795 912 C 660 912, 660 859, 522 859" stroke="#303a36" stroke-width="3" fill="none" marker-end="url(#arrow-slate)" />')

    # ================= BOTTOM BAR =================
    # Bottom bar: 'Put specific hosts above wildcards; ssh -G hostname prints the effective result'
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="50" y="1030" width="1500" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <use href="#icon-key" x="75" y="1042" />')
    svg.append('    <text x="150" y="1078" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Put specific hosts above wildcards; ssh -G hostname prints the effective result</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == '__main__':
    svg_str = generate_svg()
    out_path = pathlib.Path("candidate_p3_0105.svg")
    out_path.write_text(svg_str)
    print(f"Wrote {out_path} ({len(svg_str)} bytes)")
