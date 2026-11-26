#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

def build_perfect_svg():
    W = 1600
    H = 1010

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    lines.append('  <title>Which timestamp changes when you do what to a file</title>')
    lines.append('  <desc>A matrix showing how mtime, ctime, and atime change across common file operations in Linux.</desc>')
    lines.append('')
    lines.append('  <!-- Canvas Background -->')
    lines.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')
    lines.append('')
    lines.append('  <!-- Title: 48px bold -->')
    lines.append('  <text x="800" y="52" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#207448">Which timestamp changes when you do what to a file</text>')
    lines.append('')
    lines.append('  <!-- Legend: in its own row below the title, with >= 40px gap to matrix -->')
    lines.append('  <rect x="480" y="72" width="640" height="60" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <circle cx="580" cy="102" r="13" fill="#207448" />')
    lines.append('  <text x="606" y="110" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#303a36">changes</text>')
    lines.append('  <circle cx="840" cy="102" r="13" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    lines.append('  <text x="866" y="110" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="#303a36">unchanged</text>')
    lines.append('')
    lines.append('  <!-- Matrix Outer Container -->')
    lines.append('  <rect x="40" y="172" width="1140" height="678" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('')

    # Columns:
    # Action col: 40 to 340 (w=300)
    # Col 1 (mtime): 340 to 620 (w=280, center=480)
    # Col 2 (ctime): 620 to 900 (w=280, center=760)
    # Col 3 (atime): 900 to 1180 (w=280, center=1040)

    # Header Row: y = 172 to 330 (h = 158)
    lines.append('  <!-- Matrix Header Row -->')
    lines.append('  <rect x="40" y="172" width="1140" height="158" rx="14" fill="#e8f1ea" />')
    lines.append('  <!-- Column divider lines -->')
    lines.append('  <line x1="340" y1="172" x2="340" y2="850" stroke="#207448" stroke-width="2" />')
    lines.append('  <line x1="620" y1="172" x2="620" y2="850" stroke="#207448" stroke-width="2" />')
    lines.append('  <line x1="900" y1="172" x2="900" y2="850" stroke="#207448" stroke-width="2" />')
    lines.append('  <line x1="40" y1="330" x2="1180" y2="330" stroke="#207448" stroke-width="2" />')
    lines.append('')

    # Action col header icon (CLI / terminal icon)
    lines.append('  <!-- Action Column Header Icon -->')
    lines.append('  <g transform="translate(165, 218)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="0" y="0" width="50" height="42" rx="6" fill="#ffffff" />')
    lines.append('    <line x1="0" y1="14" x2="50" y2="14" />')
    lines.append('    <polyline points="10,24 16,28 10,32" />')
    lines.append('    <line x1="22" y1="32" x2="34" y2="32" />')
    lines.append('  </g>')

    # Column 1 Header: mtime (contents written)
    # Icon: Document with written lines
    lines.append('  <!-- Col 1 Header: mtime -->')
    lines.append('  <g transform="translate(462, 186)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 0 0 L 24 0 L 36 12 L 36 40 L 0 40 Z" fill="#ffffff" />')
    lines.append('    <polyline points="24,0 24,12 36,12" />')
    lines.append('    <line x1="8" y1="18" x2="28" y2="18" />')
    lines.append('    <line x1="8" y1="25" x2="28" y2="25" />')
    lines.append('    <line x1="8" y1="32" x2="20" y2="32" />')
    lines.append('  </g>')
    lines.append('  <text x="480" y="254" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="480" dy="0">mtime </tspan>')
    lines.append('    <tspan x="480" dy="28">(contents </tspan>')
    lines.append('    <tspan x="480" dy="28">written)</tspan>')
    lines.append('  </text>')

    # Column 2 Header: ctime (inode changed)
    # Icon: Inode / metadata block
    lines.append('  <!-- Col 2 Header: ctime -->')
    lines.append('  <g transform="translate(742, 186)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="0" y="2" width="36" height="36" rx="6" fill="#ffffff" />')
    lines.append('    <circle cx="18" cy="20" r="7" />')
    lines.append('    <line x1="18" y1="6" x2="18" y2="10" />')
    lines.append('    <line x1="18" y1="30" x2="18" y2="34" />')
    lines.append('    <line x1="4" y1="20" x2="8" y2="20" />')
    lines.append('    <line x1="28" y1="20" x2="32" y2="20" />')
    lines.append('  </g>')
    lines.append('  <text x="760" y="254" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="760" dy="0">ctime </tspan>')
    lines.append('    <tspan x="760" dy="28">(inode </tspan>')
    lines.append('    <tspan x="760" dy="28">changed)</tspan>')
    lines.append('  </text>')

    # Column 3 Header: atime (file read)
    # Icon: Eye outline
    lines.append('  <!-- Col 3 Header: atime -->')
    lines.append('  <g transform="translate(1020, 188)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <path d="M 0 18 Q 20 2 40 18 Q 20 34 0 18 Z" fill="#ffffff" />')
    lines.append('    <circle cx="20" cy="18" r="7" fill="#207448" />')
    lines.append('    <circle cx="20" cy="18" r="2.5" fill="#ffffff" />')
    lines.append('  </g>')
    lines.append('  <text x="1040" y="254" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#207448">')
    lines.append('    <tspan x="1040" dy="0">atime </tspan>')
    lines.append('    <tspan x="1040" dy="28">(file read)</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Row 1: echo more >> f1
    # y = 330 to 420 (h = 90)
    lines.append('  <!-- Row 1: echo more >> f1 -->')
    lines.append('  <line x1="40" y1="420" x2="1180" y2="420" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="65" y="382" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">echo more &gt;&gt; f1</text>')
    # mtime: filled, ctime: filled, atime: hollow
    lines.append('  <circle cx="480" cy="375" r="14" fill="#207448" />')
    lines.append('  <circle cx="760" cy="375" r="14" fill="#207448" />')
    lines.append('  <circle cx="1040" cy="375" r="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    lines.append('')

    # Row 2: chmod 600 f1
    # y = 420 to 510 (h = 90)
    # ORANGE OUTLINE on chmod row's ctime cell!
    lines.append('  <!-- Row 2: chmod 600 f1 (orange outline on ctime cell) -->')
    lines.append('  <line x1="40" y1="510" x2="1180" y2="510" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="65" y="472" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">chmod 600 f1</text>')
    # mtime: hollow
    lines.append('  <circle cx="480" cy="465" r="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # ctime: filled, with orange outline box on cell
    lines.append('  <rect x="626" y="426" width="268" height="78" rx="8" fill="#fff9f3" stroke="#db8129" stroke-width="3" />')
    lines.append('  <circle cx="760" cy="465" r="14" fill="#207448" />')
    # atime: hollow
    lines.append('  <circle cx="1040" cy="465" r="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    lines.append('')

    # Row 3: cat f1
    # y = 510 to 610 (h = 100)
    # atime: rarely: relatime
    lines.append('  <!-- Row 3: cat f1 -->')
    lines.append('  <line x1="40" y1="610" x2="1180" y2="610" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="65" y="567" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">cat f1</text>')
    # mtime: hollow, ctime: hollow
    lines.append('  <circle cx="480" cy="560" r="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    lines.append('  <circle cx="760" cy="560" r="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # atime: hollow circle with text 'rarely: relatime'
    lines.append('  <circle cx="1040" cy="542" r="13" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    lines.append('  <text x="1040" y="582" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">rarely: relatime</text>')
    lines.append('')

    # Row 4: ln f1 f2
    # y = 610 to 700 (h = 90)
    lines.append('  <!-- Row 4: ln f1 f2 -->')
    lines.append('  <line x1="40" y1="700" x2="1180" y2="700" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <text x="65" y="662" font-family="ui-monospace, monospace" font-size="25" font-weight="bold" fill="#303a36">ln f1 f2</text>')
    # mtime: hollow, ctime: filled, atime: hollow
    lines.append('  <circle cx="480" cy="655" r="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    lines.append('  <circle cx="760" cy="655" r="14" fill="#207448" />')
    lines.append('  <circle cx="1040" cy="655" r="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    lines.append('')

    # Row 5: touch -d "2026-01-01 12:00" f1
    # y = 700 to 850 (h = 150)
    lines.append('  <!-- Row 5: touch -d "2026-01-01 12:00" f1 -->')
    lines.append('  <text x="65" y="744" font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#303a36">')
    lines.append('    <tspan x="65" dy="0">touch -d </tspan>')
    lines.append('    <tspan x="65" dy="32">"2026-01-01 </tspan>')
    lines.append('    <tspan x="65" dy="32">12:00" f1</tspan>')
    lines.append('  </text>')
    # mtime: filled
    lines.append('  <circle cx="480" cy="775" r="14" fill="#207448" />')
    # ctime: filled, labelled 'ctime still moves, cannot be set'
    lines.append('  <circle cx="760" cy="728" r="13" fill="#207448" />')
    lines.append('  <text x="760" y="764" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
    lines.append('    <tspan x="760" dy="0">ctime still </tspan>')
    lines.append('    <tspan x="760" dy="28">moves, </tspan>')
    lines.append('    <tspan x="760" dy="28">cannot be set</tspan>')
    lines.append('  </text>')
    # atime: filled
    lines.append('  <circle cx="1040" cy="775" r="14" fill="#207448" />')
    lines.append('')

    # Right side box:
    # x = 1220 to 1560 (w = 340), y = 172 to 850 (h = 678)
    lines.append('  <!-- Right Side Box: stat and ls commands -->')
    lines.append('  <rect x="1220" y="172" width="340" height="678" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    lines.append('  <rect x="1220" y="172" width="340" height="92" rx="14" fill="#e8f1ea" />')
    lines.append('  <g transform="translate(1365, 196)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="0" y="0" width="50" height="42" rx="6" fill="#ffffff" />')
    lines.append('    <line x1="0" y1="14" x2="50" y2="14" />')
    lines.append('    <circle cx="8" cy="7" r="1.5" fill="#207448" />')
    lines.append('    <circle cx="15" cy="7" r="1.5" fill="#207448" />')
    lines.append('    <circle cx="22" cy="7" r="1.5" fill="#207448" />')
    lines.append('    <polyline points="10,24 16,28 10,32" />')
    lines.append('    <line x1="22" y1="32" x2="34" y2="32" />')
    lines.append('  </g>')

    # 4 sub-cards for stat and ls commands
    lines.append('  <rect x="1238" y="282" width="304" height="124" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <rect x="1238" y="422" width="304" height="96" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <rect x="1238" y="534" width="304" height="96" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    lines.append('  <rect x="1238" y="646" width="304" height="96" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')

    lines.append('  <!-- Right Box Text as single text element spanning the 4 cards -->')
    lines.append('  <text font-family="system-ui, -apple-system, sans-serif" font-size="25" fill="#303a36" text-anchor="middle">')
    lines.append('    <tspan x="1390" y="334" font-weight="bold">stat shows </tspan>')
    lines.append('    <tspan x="1390" y="370" font-weight="bold">all three; </tspan>')
    lines.append('    <tspan x="1390" y="478" font-family="ui-monospace, monospace" font-weight="bold">ls -l shows mtime, </tspan>')
    lines.append('    <tspan x="1390" y="590" font-family="ui-monospace, monospace" font-weight="bold">ls -lc ctime, </tspan>')
    lines.append('    <tspan x="1390" y="702" font-family="ui-monospace, monospace" font-weight="bold">ls -lu atime</tspan>')
    lines.append('  </text>')
    lines.append('')

    # Bottom Takeaway Green Bar:
    # x = 40, y = 890, width = 1520, height = 74
    # 'ctime is not the creation time'
    lines.append('  <!-- Bottom Takeaway Bar: ctime is not the creation time -->')
    lines.append('  <rect x="40" y="890" width="1520" height="74" rx="12" fill="#207448" />')
    lines.append('  <text x="800" y="936" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#ffffff">ctime is not the creation time</text>')
    lines.append('')
    lines.append('</svg>')

    return '\n'.join(lines)

if __name__ == '__main__':
    svg = build_perfect_svg()
    pathlib.Path('planning/image_tools/candidate_timestamps.svg').write_text(svg)
    print("Saved candidate_timestamps.svg")
