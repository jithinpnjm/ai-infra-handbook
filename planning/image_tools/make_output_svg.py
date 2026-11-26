import xml.etree.ElementTree as ET
import re

def create_svg():
    # Widths and positions
    # Margins: 40 left, 40 right. Total usable = 1520.
    # 7 boxes, 6 gaps of 40 = 240.
    # Total width of boxes = 1280.
    # Box widths:
    # 0: 138
    # 1: 224
    # 2: 178
    # 3: 178
    # 4: 164
    # 5: 220
    # 6: 178
    # Sum: 138+224+178+178+164+220+178 = 1280.

    boxes_meta = [
        {"id": "0", "w": 138, "label": "0", "title": "Success"},
        {"id": "1", "w": 224, "label": "1", "title": "General error. For grep, diff and cmp: no match or files differ, not an error"},
        {"id": "2", "w": 178, "label": "2", "title": "Misuse of a command, or a real error for grep and diff"},
        {"id": "126", "w": 178, "label": "126", "title": "Found but not executable"},
        {"id": "127", "w": 164, "label": "127", "title": "Command not found"},
        {"id": "signals", "w": 220, "label": "128 + N", "title": "signals"},
        {"id": "255", "w": 178, "label": "255", "title": "Status out of range, or ssh connection failure"},
    ]

    cur_x = 40
    gap = 40
    for b in boxes_meta:
        b["x"] = cur_x
        b["cx"] = cur_x + b["w"] / 2.0
        cur_x += b["w"] + gap

    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1000" width="1600" height="1000">')
    svg.append('  <title>Exit codes tell you what happened, from 0 for success to 128 plus N for a signal</title>')
    svg.append('  <desc>Visual infographic explaining Linux exit codes along a horizontal number line from 0 to 255, highlighting success at 0, general errors, command execution issues, 128 plus N signals, and out of range errors.</desc>')
    svg.append('')
    svg.append('  <!-- Background -->')
    svg.append('  <rect width="1600" height="1000" fill="#f5f8f5"/>')
    svg.append('')
    svg.append('  <!-- Title -->')
    svg.append('  <text x="800" y="65" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Exit codes tell you what happened,</tspan>')
    svg.append('    <tspan x="800" dy="56">from 0 for success to 128 plus N for a signal</tspan>')
    svg.append('  </text>')
    svg.append('')
    svg.append('  <!-- Horizontal Number Line Background -->')
    svg.append('  <g id="number-line">')
    svg.append('    <!-- Base track -->')
    svg.append('    <rect x="40" y="175" width="1520" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append(f'    <!-- Coloured segment 0 (Success) -->')
    svg.append(f'    <rect x="{boxes_meta[0]["x"]}" y="175" width="{boxes_meta[0]["w"]}" height="80" rx="14" fill="#d8ebd9" stroke="#207448" stroke-width="2"/>')
    svg.append(f'    <!-- Coloured segment 128+N (Signals) with Orange Outline -->')
    svg.append(f'    <rect x="{boxes_meta[5]["x"]}" y="175" width="{boxes_meta[5]["w"]}" height="80" rx="14" fill="#fff4e8" stroke="#db8129" stroke-width="3.5"/>')
    svg.append('')
    svg.append('    <!-- Marker Badges on the Line -->')
    
    # Badge 0
    c0 = boxes_meta[0]["cx"]
    svg.append(f'    <circle cx="{c0:.1f}" cy="215" r="26" fill="#ffffff" stroke="#207448" stroke-width="3"/>')
    svg.append(f'    <text x="{c0:.1f}" y="226" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#207448">0</text>')
    svg.append('')

    # Badge 1
    c1 = boxes_meta[1]["cx"]
    svg.append(f'    <circle cx="{c1:.1f}" cy="215" r="26" fill="#ffffff" stroke="#207448" stroke-width="3"/>')
    svg.append(f'    <text x="{c1:.1f}" y="226" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#303a36">1</text>')
    svg.append('')

    # Badge 2
    c2 = boxes_meta[2]["cx"]
    svg.append(f'    <circle cx="{c2:.1f}" cy="215" r="26" fill="#ffffff" stroke="#207448" stroke-width="3"/>')
    svg.append(f'    <text x="{c2:.1f}" y="226" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#303a36">2</text>')
    svg.append('')

    # Badge 126
    c3 = boxes_meta[3]["cx"]
    svg.append(f'    <rect x="{c3 - 42:.1f}" y="191" width="84" height="48" rx="10" fill="#ffffff" stroke="#207448" stroke-width="3"/>')
    svg.append(f'    <text x="{c3:.1f}" y="225" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#303a36">126</text>')
    svg.append('')

    # Badge 127
    c4 = boxes_meta[4]["cx"]
    svg.append(f'    <rect x="{c4 - 42:.1f}" y="191" width="84" height="48" rx="10" fill="#ffffff" stroke="#207448" stroke-width="3"/>')
    svg.append(f'    <text x="{c4:.1f}" y="225" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#303a36">127</text>')
    svg.append('')

    # Badge 128 + N
    c5 = boxes_meta[5]["cx"]
    svg.append(f'    <text x="{c5:.1f}" y="225" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#db8129">128 + N</text>')
    svg.append('')

    # Badge 255
    c6 = boxes_meta[6]["cx"]
    svg.append(f'    <rect x="{c6 - 42:.1f}" y="191" width="84" height="48" rx="10" fill="#ffffff" stroke="#207448" stroke-width="3"/>')
    svg.append(f'    <text x="{c6:.1f}" y="225" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="28" font-weight="bold" fill="#303a36">255</text>')
    svg.append('  </g>')
    svg.append('')

    # Leader Lines
    svg.append('  <!-- Leader Lines down to Boxes -->')
    svg.append('  <g id="leader-lines" stroke="#207448" stroke-width="3" stroke-linecap="round">')
    for i, b in enumerate(boxes_meta):
        cx = b["cx"]
        stroke_attr = ' stroke="#db8129"' if b["id"] == "signals" else ''
        svg.append(f'    <line x1="{cx:.1f}" y1="255" x2="{cx:.1f}" y2="320"{stroke_attr}/>')
    svg.append('  </g>')
    svg.append('')

    # Text Boxes
    svg.append('  <!-- Row of Text Boxes Beneath the Line -->')
    svg.append('  <g id="text-boxes">')

    # Box 0
    b0 = boxes_meta[0]
    svg.append('    <!-- Box 0: Success (Green Box) -->')
    svg.append('    <g id="box-0">')
    svg.append(f'      <rect x="{b0["x"]}" y="320" width="{b0["w"]}" height="530" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>')
    svg.append(f'      <!-- Icon: Checkmark in Circle (about 56px, stroke 4) -->')
    svg.append(f'      <g transform="translate({b0["cx"] - 28:.1f}, 350)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <circle cx="28" cy="28" r="26" fill="#ffffff"/>')
    svg.append('        <polyline points="16,28 24,36 40,20"/>')
    svg.append('      </g>')
    svg.append(f'      <text x="{b0["cx"]:.1f}" y="475" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">Success</text>')
    svg.append('    </g>')
    svg.append('')

    # Box 1
    b1 = boxes_meta[1]
    svg.append('    <!-- Box 1: General error -->')
    svg.append('    <g id="box-1">')
    svg.append(f'      <rect x="{b1["x"]}" y="320" width="{b1["w"]}" height="530" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append(f'      <!-- Icon: Warning Triangle (about 56px, stroke 4) -->')
    svg.append(f'      <g transform="translate({b1["cx"] - 28:.1f}, 350)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <path d="M 28 6 L 52 48 L 4 48 Z" fill="#e8f1ea"/>')
    svg.append('        <line x1="28" y1="20" x2="28" y2="32"/>')
    svg.append('        <circle cx="28" cy="40" r="2" fill="#207448"/>')
    svg.append('      </g>')
    svg.append(f'      <text x="{b1["cx"]:.1f}" y="445" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'        <tspan x="{b1["cx"]:.1f}" dy="0">General</tspan>')
    svg.append(f'        <tspan x="{b1["cx"]:.1f}" dy="34">error. For</tspan>')
    svg.append(f'        <tspan x="{b1["cx"]:.1f}" dy="34">grep, diff</tspan>')
    svg.append(f'        <tspan x="{b1["cx"]:.1f}" dy="34">and cmp: no</tspan>')
    svg.append(f'        <tspan x="{b1["cx"]:.1f}" dy="34">match or</tspan>')
    svg.append(f'        <tspan x="{b1["cx"]:.1f}" dy="34">files differ,</tspan>')
    svg.append(f'        <tspan x="{b1["cx"]:.1f}" dy="34">not an error</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('')

    # Box 2
    b2 = boxes_meta[2]
    svg.append('    <!-- Box 2: Misuse of a command -->')
    svg.append('    <g id="box-2">')
    svg.append(f'      <rect x="{b2["x"]}" y="320" width="{b2["w"]}" height="530" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append(f'      <!-- Icon: Gear / Command syntax (about 56px, stroke 4) -->')
    svg.append(f'      <g transform="translate({b2["cx"] - 28:.1f}, 350)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <rect x="4" y="8" width="48" height="40" rx="6" fill="#e8f1ea"/>')
    svg.append('        <polyline points="14,22 22,28 14,34"/>')
    svg.append('        <line x1="26" y1="34" x2="38" y2="34"/>')
    svg.append('      </g>')
    svg.append(f'      <text x="{b2["cx"]:.1f}" y="455" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'        <tspan x="{b2["cx"]:.1f}" dy="0">Misuse of</tspan>')
    svg.append(f'        <tspan x="{b2["cx"]:.1f}" dy="34">a command,</tspan>')
    svg.append(f'        <tspan x="{b2["cx"]:.1f}" dy="34">or a real</tspan>')
    svg.append(f'        <tspan x="{b2["cx"]:.1f}" dy="34">error for</tspan>')
    svg.append(f'        <tspan x="{b2["cx"]:.1f}" dy="34">grep and</tspan>')
    svg.append(f'        <tspan x="{b2["cx"]:.1f}" dy="34">diff</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('')

    # Box 126
    b3 = boxes_meta[3]
    svg.append('    <!-- Box 3: Found but not executable -->')
    svg.append('    <g id="box-126">')
    svg.append(f'      <rect x="{b3["x"]}" y="320" width="{b3["w"]}" height="530" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append(f'      <!-- Icon: File with Lock (about 56px, stroke 4) -->')
    svg.append(f'      <g transform="translate({b3["cx"] - 27:.1f}, 350)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <path d="M 8 4 L 32 4 L 46 18 L 46 52 L 8 52 Z" fill="#e8f1ea"/>')
    svg.append('        <circle cx="27" cy="34" r="7"/>')
    svg.append('        <path d="M 23 34 L 23 27 C 23 24 31 24 31 27 L 31 34"/>')
    svg.append('      </g>')
    svg.append(f'      <text x="{b3["cx"]:.1f}" y="490" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'        <tspan x="{b3["cx"]:.1f}" dy="0">Found but</tspan>')
    svg.append(f'        <tspan x="{b3["cx"]:.1f}" dy="34">not</tspan>')
    svg.append(f'        <tspan x="{b3["cx"]:.1f}" dy="34">executable</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('')

    # Box 127
    b4 = boxes_meta[4]
    svg.append('    <!-- Box 4: Command not found -->')
    svg.append('    <g id="box-127">')
    svg.append(f'      <rect x="{b4["x"]}" y="320" width="{b4["w"]}" height="530" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append(f'      <!-- Icon: Search with Question / Missing (about 56px, stroke 4) -->')
    svg.append(f'      <g transform="translate({b4["cx"] - 28:.1f}, 350)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <circle cx="24" cy="24" r="16" fill="#e8f1ea"/>')
    svg.append('        <line x1="36" y1="36" x2="48" y2="48"/>')
    svg.append('        <line x1="18" y1="18" x2="30" y2="30"/>')
    svg.append('        <line x1="30" y1="18" x2="18" y2="30"/>')
    svg.append('      </g>')
    svg.append(f'      <text x="{b4["cx"]:.1f}" y="505" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'        <tspan x="{b4["cx"]:.1f}" dy="0">Command</tspan>')
    svg.append(f'        <tspan x="{b4["cx"]:.1f}" dy="34">not found</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('')

    # Box 5: signals
    b5 = boxes_meta[5]
    svg.append('    <!-- Box 5: 128 + N Segment / Signals Box (Orange Outline) -->')
    svg.append('    <g id="box-signals">')
    svg.append(f'      <rect x="{b5["x"]}" y="320" width="{b5["w"]}" height="530" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3"/>')
    svg.append(f'      <!-- Icon: Signal lightning / pulse (about 56px, orange stroke 4) -->')
    svg.append(f'      <g transform="translate({b5["cx"] - 27:.1f}, 350)" fill="none" stroke="#db8129" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <polygon points="30,4 12,28 26,28 22,52 42,24 28,24" fill="#fff4e8"/>')
    svg.append('      </g>')
    svg.append('      <!-- 3 Small Markers inside 128+N box -->')
    
    # Sub-box width 204, centered inside b5["w"]=220 -> margin 8px each side
    sub_w = 204
    sub_x = b5["x"] + (b5["w"] - sub_w) / 2.0
    svg.append(f'      <rect x="{sub_x:.1f}" y="440" width="{sub_w}" height="60" rx="10" fill="#fff8f2" stroke="#db8129" stroke-width="1.5"/>')
    svg.append(f'      <text x="{b5["cx"]:.1f}" y="478" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">130 Ctrl-C</text>')
    svg.append('')
    svg.append(f'      <rect x="{sub_x:.1f}" y="525" width="{sub_w}" height="60" rx="10" fill="#fff8f2" stroke="#db8129" stroke-width="1.5"/>')
    svg.append(f'      <text x="{b5["cx"]:.1f}" y="563" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">137 SIGKILL</text>')
    svg.append('')
    svg.append(f'      <rect x="{sub_x:.1f}" y="610" width="{sub_w}" height="60" rx="10" fill="#fff8f2" stroke="#db8129" stroke-width="1.5"/>')
    svg.append(f'      <text x="{b5["cx"]:.1f}" y="648" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">143 SIGTERM</text>')
    svg.append('    </g>')
    svg.append('')

    # Box 6: 255
    b6 = boxes_meta[6]
    svg.append('    <!-- Box 6: 255 Status out of range -->')
    svg.append('    <g id="box-255">')
    svg.append(f'      <rect x="{b6["x"]}" y="320" width="{b6["w"]}" height="530" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append(f'      <!-- Icon: Shield / Connection Warning (about 56px, stroke 4) -->')
    svg.append(f'      <g transform="translate({b6["cx"] - 28:.1f}, 350)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('        <path d="M 28 6 L 48 14 L 48 30 C 48 42 28 50 28 50 C 28 50 8 42 8 30 L 8 14 Z" fill="#e8f1ea"/>')
    svg.append('        <line x1="28" y1="20" x2="28" y2="34"/>')
    svg.append('        <circle cx="28" cy="40" r="1.5" fill="#207448"/>')
    svg.append('      </g>')
    svg.append(f'      <text x="{b6["cx"]:.1f}" y="465" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'        <tspan x="{b6["cx"]:.1f}" dy="0">Status out</tspan>')
    svg.append(f'        <tspan x="{b6["cx"]:.1f}" dy="34">of range,</tspan>')
    svg.append(f'        <tspan x="{b6["cx"]:.1f}" dy="34">or ssh</tspan>')
    svg.append(f'        <tspan x="{b6["cx"]:.1f}" dy="34">connection</tspan>')
    svg.append(f'        <tspan x="{b6["cx"]:.1f}" dy="34">failure</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('  </g>')
    svg.append('')

    # Caption / Takeaway Bar
    svg.append('  <!-- Takeaway / Caption Bar at Bottom -->')
    svg.append('  <g id="caption-bar">')
    svg.append('    <rect x="40" y="890" width="1520" height="66" rx="12" fill="#207448"/>')
    svg.append('    <text x="800" y="932" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Read the code, then check which program produced it.</text>')
    svg.append('  </g>')
    svg.append('</svg>')

    return "\n".join(svg), boxes_meta

svg_str, meta = create_svg()
with open("output.svg", "w", encoding="utf-8") as f:
    f.write(svg_str)
print("Saved output.svg successfully!")
