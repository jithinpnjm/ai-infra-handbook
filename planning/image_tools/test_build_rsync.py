#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_svg():
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
    svg.append('  <title>The rsync trailing slash: contents versus the directory itself</title>')
    svg.append('  <desc>Visual infographic explaining the difference between rsync with and without a trailing slash, scp directory nesting, and a safe dry-run deletion routine.</desc>')

    # Defs: Outline Icons (56x56 px, stroke 4, fill none)
    svg.append('  <defs>')
    # Folder / Directory outline icon
    svg.append('    <g id="icon-folder" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 6 12 L 22 12 L 28 18 L 50 18 C 52 18 54 20 54 22 L 54 44 C 54 46 52 48 50 48 L 6 48 C 4 48 2 46 2 44 L 2 16 C 2 14 4 12 6 12 Z" fill="#ffffff" />')
    svg.append('      <line x1="2" y1="22" x2="54" y2="22" />')
    svg.append('    </g>')

    # Server / Storage disk outline icon
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

    # File item outline icon
    svg.append('    <g id="icon-file" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 6 4 L 24 4 L 34 14 L 34 40 C 34 42 32 44 30 44 L 6 44 C 4 44 2 42 2 40 L 2 8 C 2 6 4 4 6 4 Z" fill="#ffffff" />')
    svg.append('      <polyline points="24,4 24,14 34,14" />')
    svg.append('    </g>')

    # Alert triangle outline icon
    svg.append('    <g id="icon-alert" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 52 48 L 4 48 Z" fill="#ffffff" />')
    svg.append('      <line x1="28" y1="20" x2="28" y2="32" />')
    svg.append('      <circle cx="28" cy="40" r="2" fill="#207448" />')
    svg.append('    </g>')

    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="{BG}" />')

    # Title: 48px bold
    svg.append('  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">The rsync trailing slash: </tspan>')
    svg.append('    <tspan x="800" dy="54">contents versus the directory itself</tspan>')
    svg.append('  </text>')

    # ==================== TOP SETUP ROW ====================
    # Outer panel
    svg.append('  <rect x="40" y="145" width="1520" height="150" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

    # Source Box: directory 'data' containing 'a.pt' and 'b.pt'
    svg.append('  <g id="source-box">')
    svg.append('    <rect x="60" y="165" width="700" height="110" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
    svg.append('    <use href="#icon-folder" x="80" y="192" />')
    svg.append('    <text x="155" y="228" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">data</text>')
    # File a.pt
    svg.append('    <rect x="330" y="185" width="185" height="70" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <use href="#icon-file" x="345" y="198" />')
    svg.append('    <text x="440" y="228" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">a.pt</text>')
    # File b.pt
    svg.append('    <rect x="545" y="185" width="185" height="70" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <use href="#icon-file" x="560" y="198" />')
    svg.append('    <text x="655" y="228" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">b.pt</text>')
    svg.append('  </g>')

    # Destination Box: existing directory '/scratch/data' on gpu01
    svg.append('  <g id="dest-box">')
    svg.append('    <rect x="840" y="165" width="700" height="110" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
    svg.append('    <use href="#icon-server" x="865" y="192" />')
    svg.append('    <text x="945" y="230" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">/scratch/data</text>')
    svg.append('  </g>')

    # ==================== THREE RESULT CARDS ====================
    # Card A: 'rsync -a data/ gpu01:/scratch/data'
    svg.append('  <g id="card-a">')
    svg.append('    <rect x="40" y="335" width="480" height="410" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Command Box
    svg.append('    <rect x="60" y="355" width="440" height="90" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="280" y="391" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">')
    svg.append('      <tspan x="280" dy="0">rsync -a data/ </tspan>')
    svg.append('      <tspan x="280" dy="33">gpu01:/scratch/data</tspan>')
    svg.append('    </text>')
    # Result tree: /scratch/data/a.pt
    svg.append('    <rect x="60" y="455" width="440" height="58" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="280" y="492" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">/scratch/data/a.pt</text>')
    # Result tree: /scratch/data/b.pt
    svg.append('    <rect x="60" y="523" width="440" height="58" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="280" y="560" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">/scratch/data/b.pt</text>')
    # Note badge: contents copied into the destination
    svg.append('    <rect x="60" y="595" width="440" height="130" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="280" y="645" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="280" dy="0">contents copied </tspan>')
    svg.append('      <tspan x="280" dy="35">into the destination</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Card B: 'rsync -a data gpu01:/scratch/data' (Orange outline - common mistake)
    svg.append('  <g id="card-b">')
    svg.append('    <rect x="560" y="335" width="480" height="410" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    # Command Box
    svg.append('    <rect x="580" y="355" width="440" height="90" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="800" y="391" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="800" dy="0">rsync -a data </tspan>')
    svg.append('      <tspan x="800" dy="33">gpu01:/scratch/data</tspan>')
    svg.append('    </text>')
    # Result tree: /scratch/data/data/a.pt
    svg.append('    <rect x="580" y="455" width="440" height="58" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="800" y="492" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">/scratch/data/data/a.pt</text>')
    # Result tree: /scratch/data/data/b.pt
    svg.append('    <rect x="580" y="523" width="440" height="58" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="800" y="560" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">/scratch/data/data/b.pt</text>')
    # Note badge: the directory itself, nested copy
    svg.append('    <rect x="580" y="595" width="440" height="130" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="800" y="645" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="800" dy="0">the directory itself, </tspan>')
    svg.append('      <tspan x="800" dy="35">nested copy</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Card C: 'scp -r data gpu01:/scratch/data'
    svg.append('  <g id="card-c">')
    svg.append('    <rect x="1080" y="335" width="480" height="410" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Command Box
    svg.append('    <rect x="1100" y="355" width="440" height="90" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1320" y="391" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="1320" dy="0">scp -r data </tspan>')
    svg.append('      <tspan x="1320" dy="33">gpu01:/scratch/data</tspan>')
    svg.append('    </text>')
    # Result tree: /scratch/data/data/a.pt
    svg.append('    <rect x="1100" y="455" width="440" height="58" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1320" y="492" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">/scratch/data/data/a.pt</text>')
    # Result tree: /scratch/data/data/b.pt
    svg.append('    <rect x="1100" y="523" width="440" height="58" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1320" y="560" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">/scratch/data/data/b.pt</text>')
    # Note badge: also copies every byte again, even when nothing changed
    svg.append('    <rect x="1100" y="595" width="440" height="130" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('    <text x="1320" y="634" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1320" dy="0">also copies every </tspan>')
    svg.append('      <tspan x="1320" dy="30">byte again, even </tspan>')
    svg.append('      <tspan x="1320" dy="30">when nothing changed</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== SAFETY STRIP ====================
    # Outer container
    svg.append('  <rect x="40" y="785" width="1520" height="325" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

    # Step 1: 'rsync -avhn --delete data/ gpu01:/scratch/data/ (dry run)'
    svg.append('  <g id="step-1">')
    svg.append('    <rect x="60" y="805" width="760" height="145" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
    svg.append('    <circle cx="102" cy="877" r="24" fill="#207448" />')
    svg.append('    <text x="102" y="886" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>')
    svg.append('    <text x="465" y="860" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">')
    svg.append('      <tspan x="465" dy="0">rsync -avhn --delete </tspan>')
    svg.append('      <tspan x="465" dy="34">data/ gpu01:/scratch/data/ (dry run)</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Step 2: 'read the list'
    svg.append('  <g id="step-2">')
    svg.append('    <rect x="840" y="805" width="320" height="145" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
    svg.append('    <circle cx="882" cy="877" r="24" fill="#207448" />')
    svg.append('    <text x="882" y="886" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>')
    svg.append('    <text x="1035" y="886" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">read the list</text>')
    svg.append('  </g>')

    # Step 3: 'run again without -n'
    svg.append('  <g id="step-3">')
    svg.append('    <rect x="1180" y="805" width="360" height="145" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
    svg.append('    <circle cx="1222" cy="877" r="24" fill="#207448" />')
    svg.append('    <text x="1222" y="886" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>')
    svg.append('    <text x="1380" y="865" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="1380" dy="0">run again </tspan>')
    svg.append('      <tspan x="1380" dy="30">without -n</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Warning note: '--delete makes the destination match the source; an empty source deletes the destination contents'
    svg.append('  <g id="warning-strip">')
    svg.append('    <rect x="60" y="970" width="1480" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
    svg.append('    <use href="#icon-alert" x="90" y="1002" />')
    svg.append('    <text x="835" y="1024" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="835" dy="0">--delete makes the destination match the source; </tspan>')
    svg.append('      <tspan x="835" dy="32">an empty source deletes the destination contents</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

content = build_svg()
with open("test_rsync_candidate.svg", "w") as f:
    f.write(content)
print("Updated test_rsync_candidate.svg successfully!")
