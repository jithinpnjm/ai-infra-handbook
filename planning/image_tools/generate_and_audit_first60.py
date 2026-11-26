import re
import xml.etree.ElementTree as ET

svg_lines = []

def a(line):
    svg_lines.append(line)

# Build SVG
a('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
a('  <title>The first minute: ten commands, each asks one question</title>')
a('  <desc>Checklist ladder of ten Linux commands and questions in time order.</desc>')
a('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
a('  <text x="60" y="68" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The first 60 seconds, command by command</text>')
a('  <g id="clock-badge">')
a('    <circle cx="1265" cy="58" r="20" stroke="#207448" stroke-width="3.5" fill="none"/>')
a('    <line x1="1265" y1="58" x2="1265" y2="45" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>')
a('    <line x1="1265" y1="58" x2="1277" y2="58" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>')
a('    <circle cx="1265" cy="58" r="3" fill="#207448"/>')
a('    <text x="1298" y="66" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">1 second interval</text>')
a('  </g>')
a('  <g id="down-arrow">')
a('    <line x1="82" y1="90" x2="82" y2="1080" stroke="#207448" stroke-width="2.5"/>')
a('    <polygon points="75,1080 82,1098 89,1080" fill="#207448"/>')
a('    <text x="58" y="594" transform="rotate(-90 58 594)" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448" text-anchor="middle">read top to bottom</text>')
a('  </g>')
a('  <g id="bracket-cpu">')
a('    <path d="M 248 90 H 236 V 588 H 248" fill="none" stroke="#207448" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
a('    <text x="165" y="347" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448" text-anchor="middle">CPU</text>')
a('  </g>')
a('  <g id="bracket-memory-disk">')
a('    <path d="M 248 600 H 236 V 792 H 248" fill="none" stroke="#207448" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
a('    <text x="165" y="690" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448" text-anchor="middle"><tspan x="165" dy="0">Memory </tspan><tspan x="165" dy="28">and disk</tspan></text>')
a('  </g>')
a('  <g id="bracket-network">')
a('    <path d="M 248 804 H 236 V 996 H 248" fill="none" stroke="#207448" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
a('    <text x="165" y="908" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448" text-anchor="middle">Network</text>')
a('  </g>')
a('  <g id="label-sanity-check">')
a('    <text x="165" y="1047" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448" text-anchor="middle"><tspan x="165" dy="0">sanity </tspan><tspan x="165" dy="28">check</tspan></text>')
a('  </g>')

rows_data = [
    {
        "num": "1",
        "cmd": "uptime",
        "cmd_w": 290,
        "q": [("Is demand rising or falling? ", 0), ("Compare the 1, 5 and 15 minute numbers.", 26)],
        "icon": "clock"
    },
    {
        "num": "2",
        "cmd": "dmesg -T | tail",
        "cmd_w": 290,
        "q": [("Did the kernel log errors, including OOM kills?", 0)],
        "icon": "terminal"
    },
    {
        "num": "3",
        "cmd": "vmstat -SM 1",
        "cmd_w": 220,
        "callout": "first row is since boot",
        "callout_w": 355,
        "q": [("Run queue, swapping and overall ", 0), ("CPU split, one second at a time.", 26)],
        "icon": "vmstat"
    },
    {
        "num": "4",
        "cmd": "mpstat -P ALL 1",
        "cmd_w": 290,
        "q": [("Is one CPU busy while the others idle?", 0)],
        "icon": "mpstat"
    },
    {
        "num": "5",
        "cmd": "pidstat 1",
        "cmd_w": 290,
        "q": [("Which processes use the CPU, ", 0), ("and user or kernel time?", 26)],
        "icon": "pidstat"
    },
    {
        "num": "6",
        "cmd": "iostat -sxz 1",
        "cmd_w": 290,
        "q": [("Disk IOPS, throughput, wait time and percent busy.", 0)],
        "icon": "iostat"
    },
    {
        "num": "7",
        "cmd": "free -m",
        "cmd_w": 290,
        "q": [("Memory in use, including the page cache.", 0)],
        "icon": "free"
    },
    {
        "num": "8",
        "cmd": "sar -n DEV 1",
        "cmd_w": 290,
        "q": [("Network interface throughput and packets.", 0)],
        "icon": "sar_dev"
    },
    {
        "num": "9",
        "cmd": "sar -n TCP,ETCP 1",
        "cmd_w": 290,
        "q": [("TCP connection rates and retransmits.", 0)],
        "icon": "sar_tcp"
    },
    {
        "num": "10",
        "cmd": "top",
        "cmd_w": 290,
        "q": [("A sanity overview of everything above.", 0)],
        "icon": "top"
    }
]

icons_svg = {
    "clock": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="26" cy="26" r="21"/>
      <line x1="26" y1="26" x2="26" y2="13"/>
      <line x1="26" y1="26" x2="35" y2="26"/>
      <circle cx="26" cy="26" r="3" fill="#207448"/>
    </g>''',
    "terminal": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="5" y="7" width="42" height="38" rx="5"/>
      <line x1="5" y1="16" x2="47" y2="16" stroke-width="2"/>
      <path d="M 12 24 L 18 29 L 12 34" stroke-width="2.5"/>
      <line x1="23" y1="34" x2="36" y2="34" stroke-width="2.5"/>
    </g>''',
    "vmstat": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="40" height="36" rx="4"/>
      <line x1="14" y1="36" x2="14" y2="26" stroke-width="4"/>
      <line x1="26" y1="36" x2="26" y2="16" stroke-width="4"/>
      <line x1="38" y1="36" x2="38" y2="22" stroke-width="4"/>
    </g>''',
    "mpstat": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="32" height="32" rx="4"/>
      <line x1="26" y1="10" x2="26" y2="42" stroke-width="2"/>
      <line x1="10" y1="26" x2="42" y2="26" stroke-width="2"/>
      <line x1="18" y1="4" x2="18" y2="10" stroke-width="2.5"/>
      <line x1="34" y1="4" x2="34" y2="10" stroke-width="2.5"/>
      <line x1="18" y1="42" x2="18" y2="48" stroke-width="2.5"/>
      <line x1="34" y1="42" x2="34" y2="48" stroke-width="2.5"/>
      <line x1="4" y1="18" x2="10" y2="18" stroke-width="2.5"/>
      <line x1="4" y1="34" x2="10" y2="34" stroke-width="2.5"/>
      <line x1="42" y1="18" x2="48" y2="18" stroke-width="2.5"/>
      <line x1="42" y1="34" x2="48" y2="34" stroke-width="2.5"/>
    </g>''',
    "pidstat": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="7" y="7" width="38" height="38" rx="5"/>
      <circle cx="16" cy="17" r="2.5" fill="#207448"/>
      <line x1="23" y1="17" x2="38" y2="17" stroke-width="2.5"/>
      <circle cx="16" cy="26" r="2.5" fill="#207448"/>
      <line x1="23" y1="26" x2="35" y2="26" stroke-width="2.5"/>
      <circle cx="16" cy="35" r="2.5" fill="#207448"/>
      <line x1="23" y1="35" x2="37" y2="35" stroke-width="2.5"/>
    </g>''',
    "iostat": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="26" cy="13" rx="19" ry="6"/>
      <path d="M 7 13 V 26 C 7 29.5 15.5 32 26 32 C 36.5 32 45 29.5 45 26 V 13"/>
      <path d="M 7 26 V 39 C 7 42.5 15.5 45 26 45 C 36.5 45 45 42.5 45 39 V 26"/>
      <circle cx="36" cy="39" r="2" fill="#207448"/>
    </g>''',
    "free": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="7" y="15" width="38" height="22" rx="3"/>
      <rect x="12" y="19" width="6" height="9" stroke-width="1.8"/>
      <rect x="23" y="19" width="6" height="9" stroke-width="1.8"/>
      <rect x="34" y="19" width="6" height="9" stroke-width="1.8"/>
      <line x1="12" y1="37" x2="12" y2="41" stroke-width="2"/>
      <line x1="19" y1="37" x2="19" y2="41" stroke-width="2"/>
      <line x1="26" y1="37" x2="26" y2="41" stroke-width="2"/>
      <line x1="33" y1="37" x2="33" y2="41" stroke-width="2"/>
      <line x1="40" y1="37" x2="40" y2="41" stroke-width="2"/>
    </g>''',
    "sar_dev": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="9" y="9" width="34" height="32" rx="4"/>
      <path d="M 16 41 V 35 H 36 V 41" stroke-width="2"/>
      <line x1="19" y1="15" x2="19" y2="23" stroke-width="2"/>
      <line x1="23" y1="15" x2="23" y2="23" stroke-width="2"/>
      <line x1="27" y1="15" x2="27" y2="23" stroke-width="2"/>
      <line x1="31" y1="15" x2="31" y2="23" stroke-width="2"/>
      <circle cx="15" cy="28" r="2" fill="#207448"/>
      <circle cx="37" cy="28" r="2" fill="#207448"/>
    </g>''',
    "sar_tcp": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="15" cy="26" r="7"/>
      <circle cx="37" cy="26" r="7"/>
      <path d="M 22 22 H 30" stroke-width="2.5"/>
      <path d="M 22 30 H 30" stroke-width="2.5"/>
      <path d="M 6 21 A 7 7 0 0 0 6 31" stroke-width="2"/>
      <path d="M 46 21 A 7 7 0 0 1 46 31" stroke-width="2"/>
    </g>''',
    "top": '''<g transform="translate(338, {y})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="5" y="7" width="42" height="38" rx="4"/>
      <line x1="5" y1="16" x2="47" y2="16" stroke-width="1.8"/>
      <path d="M 13 32 A 7 7 0 1 1 23 32" stroke-width="2.2"/>
      <line x1="18" y1="27" x2="21" y2="22" stroke-width="2"/>
      <line x1="28" y1="22" x2="41" y2="22" stroke-width="2.2"/>
      <line x1="28" y1="29" x2="37" y2="29" stroke-width="2.2"/>
      <line x1="28" y1="36" x2="39" y2="36" stroke-width="2.2"/>
    </g>'''
}

y_start = 90
row_h = 90
gap = 12

for i, row in enumerate(rows_data):
    y = y_start + i * (row_h + gap)
    mid_y = y + row_h // 2
    a(f'  <g id="row-{row["num"]}">')
    a(f'    <rect x="260" y="{y}" width="1300" height="{row_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="1.5" stroke-opacity="0.3"/>')
    a(f'    <circle cx="300" cy="{mid_y}" r="24" fill="#207448"/>')
    a(f'    <text x="300" y="{mid_y}" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">{row["num"]}</text>')
    
    icon_code = icons_svg[row["icon"]].replace("{y}", str(y + 19))
    a(f'    {icon_code}')
    
    # Command box
    cmd_w = row["cmd_w"]
    cmd_x = 410
    cmd_mid_x = cmd_x + cmd_w // 2
    a(f'    <rect x="{cmd_x}" y="{y + 17}" width="{cmd_w}" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>')
    a(f'    <text x="{cmd_mid_x}" y="{mid_y}" text-anchor="middle" dominant-baseline="central" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">{row["cmd"]}</text>')
    
    # Callout if any
    cur_x = cmd_x + cmd_w
    if "callout" in row:
        c_w = row["callout_w"]
        c_x = cur_x + 15
        c_mid_x = c_x + c_w // 2
        a(f'    <rect x="{c_x}" y="{y + 17}" width="{c_w}" height="56" rx="8" fill="#fff9f2" stroke="#db8129" stroke-width="2.5"/>')
        a(f'    <text x="{c_mid_x}" y="{mid_y}" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">{row["callout"]}</text>')
        cur_x = c_x + c_w
    
    # Question text
    q_x = cur_x + 25
    q_lines = row["q"]
    if len(q_lines) == 1:
        a(f'    <text x="{q_x}" y="{mid_y}" dominant-baseline="central" font-family="sans-serif" font-size="24" fill="#303a36">{q_lines[0][0]}</text>')
    else:
        # 2 lines
        tspan_str = "".join([f'<tspan x="{q_x}" dy="{dy}">{txt}</tspan>' for txt, dy in q_lines])
        a(f'    <text x="{q_x}" y="{mid_y - 10}" font-family="sans-serif" font-size="24" fill="#303a36">{tspan_str}</text>')
        
    a('  </g>')

# Takeaway bar
a('  <g id="takeaway-bar">')
a('    <rect x="40" y="1110" width="1520" height="50" rx="10" fill="#207448"/>')
a('    <text x="800" y="1143" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Run the checklist top to bottom without stopping to theorise, then say what each line told you.</text>')
a('  </g>')
a('</svg>')

svg_content = "\n".join(svg_lines)
with open("output_first60.svg", "w") as f:
    f.write(svg_content)

print("Wrote output_first60.svg successfully!")
