import re
import xml.etree.ElementTree as ET

def build_svg():
    # Colors:
    # background: #f5f8f5
    # text: #303a36
    # main green: #207448
    # light green panels: #e8f1ea
    # one orange: #db8129 (used ONLY on Errors item)

    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100">')
    svg.append('  <title>The USE method applied to a NIC and its PCIe slot</title>')
    svg.append('  <desc>Visual infographic explaining the USE method (utilization, saturation, errors) for network interfaces and PCIe bandwidth bottleneck on 400G NICs.</desc>')
    svg.append('')
    svg.append('  <!-- Canvas Background -->')
    svg.append('  <rect width="1600" height="1100" fill="#f5f8f5"/>')
    svg.append('')
    svg.append('  <!-- Main Title (48px bold) -->')
    svg.append('  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The USE method applied to a NIC and its PCIe slot</text>')
    svg.append('')
    svg.append('  <!-- ========================================== -->')
    svg.append('  <!-- LEFT: 3-row USE Table Container           -->')
    svg.append('  <!-- ========================================== -->')
    svg.append('  <rect x="40" y="115" width="720" height="810" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('')

    # --- ROW 1: Utilization ---
    # Card: x=60, y=135, width=680, height=240
    svg.append('  <!-- Row 1: Utilization -->')
    svg.append('  <rect x="60" y="135" width="680" height="240" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Icon: gauge / meter (56x56 at x=85, y=155)
    svg.append('  <g transform="translate(85, 155)">')
    svg.append('    <path d="M 8 44 A 20 20 0 1 1 48 44" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round"/>')
    svg.append('    <line x1="28" y1="36" x2="40" y2="20" stroke="#207448" stroke-width="4" stroke-linecap="round"/>')
    svg.append('    <circle cx="28" cy="36" r="4" fill="#207448"/>')
    svg.append('  </g>')
    # Text: Utilization
    svg.append('  <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="155" y="193" font-size="30" font-weight="bold" fill="#207448">Utilization: </tspan>')
    svg.append('    <tspan x="85" y="245">the busy fraction = throughput divided</tspan>')
    svg.append('    <tspan x="85" y="280">by the negotiated speed, counting all</tspan>')
    svg.append('    <tspan x="85" y="315">headers; with cloud caps use the limit</tspan>')
    svg.append('    <tspan x="85" y="350">the cloud imposes</tspan>')
    svg.append('  </text>')
    svg.append('')

    # --- ROW 2: Saturation ---
    # Card: x=60, y=400, width=680, height=240
    svg.append('  <!-- Row 2: Saturation -->')
    svg.append('  <rect x="60" y="400" width="680" height="240" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Icon: buffer queue (56x56 at x=85, y=420)
    svg.append('  <g transform="translate(85, 420)">')
    svg.append('    <rect x="8" y="10" width="40" height="10" rx="3" fill="none" stroke="#207448" stroke-width="4"/>')
    svg.append('    <rect x="8" y="24" width="40" height="10" rx="3" fill="none" stroke="#207448" stroke-width="4"/>')
    svg.append('    <rect x="8" y="38" width="40" height="10" rx="3" fill="none" stroke="#207448" stroke-width="4"/>')
    svg.append('    <line x1="20" y1="10" x2="20" y2="48" stroke="#207448" stroke-width="3" stroke-dasharray="2 2"/>')
    svg.append('    <line x1="36" y1="10" x2="36" y2="48" stroke="#207448" stroke-width="3" stroke-dasharray="2 2"/>')
    svg.append('  </g>')
    # Text: Saturation
    svg.append('  <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="155" y="458" font-size="30" font-weight="bold" fill="#207448">Saturation: </tspan>')
    svg.append('    <tspan x="85" y="510">queueing: qdisc backlog and drops,</tspan>')
    svg.append('    <tspan x="85" y="545">application threads blocked on send,</tspan>')
    svg.append('    <tspan x="85" y="580">TCP retransmits as a symptom,</tspan>')
    svg.append('    <tspan x="85" y="615">NIC ring overruns</tspan>')
    svg.append('  </text>')
    svg.append('')

    # --- ROW 3: Errors (Orange) ---
    # Card: x=60, y=665, width=680, height=240
    svg.append('  <!-- Row 3: Errors (Orange - check errors first) -->')
    svg.append('  <rect x="60" y="665" width="680" height="240" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2.5"/>')
    # Icon: warning alert (56x56 at x=85, y=685) in orange
    svg.append('  <g transform="translate(85, 685)">')
    svg.append('    <path d="M 28 8 L 50 46 L 6 46 Z" fill="none" stroke="#db8129" stroke-width="4" stroke-linejoin="round"/>')
    svg.append('    <line x1="28" y1="21" x2="28" y2="33" stroke="#db8129" stroke-width="4" stroke-linecap="round"/>')
    svg.append('    <circle cx="28" cy="39" r="2.5" fill="#db8129"/>')
    svg.append('  </g>')
    # Text: Errors
    svg.append('  <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="155" y="723" font-size="30" font-weight="bold" fill="#db8129">Errors: </tspan>')
    svg.append('    <tspan x="85" y="775">on RX bad checksums and frames too short</tspan>')
    svg.append('    <tspan x="85" y="810">or too long; on TX late collisions and</tspan>')
    svg.append('    <tspan x="85" y="845">carrier errors; check errors first</tspan>')
    svg.append('  </text>')
    svg.append('')

    # --- RIGHT SIDE ---
    # Right Column: x=800, width=760
    # Top card: Worked PCIe example (x=800, y=115, width=760, height=400)
    svg.append('  <!-- ========================================== -->')
    svg.append('  <!-- RIGHT: Worked PCIe Example (Two Bars)      -->')
    svg.append('  <!-- ========================================== -->')
    svg.append('  <rect x="800" y="115" width="760" height="400" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('')

    # Bar 1: PCIe Gen4 x16 (x=820, y=135, width=720, height=170)
    svg.append('  <!-- PCIe Gen4 x16 Sub-card -->')
    svg.append('  <rect x="820" y="135" width="720" height="170" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Icon: PCIe card (56x56 at x=840, y=148)
    svg.append('  <g transform="translate(840, 148)">')
    svg.append('    <rect x="8" y="10" width="40" height="26" rx="4" fill="none" stroke="#207448" stroke-width="4"/>')
    svg.append('    <path d="M 14 36 L 14 46 M 22 36 L 22 46 M 30 36 L 30 46 M 38 36 L 38 46" stroke="#207448" stroke-width="4" stroke-linecap="round"/>')
    svg.append('    <line x1="8" y1="20" x2="48" y2="20" stroke="#207448" stroke-width="3"/>')
    svg.append('  </g>')
    # Text: PCIe Gen4 x16
    svg.append('  <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="910" y="180" font-size="30" font-weight="bold" fill="#207448">PCIe Gen4 x16: </tspan>')
    svg.append('    <tspan x="840" y="218">about 252 Gb/s usable; one 400G NIC in that</tspan>')
    svg.append('    <tspan x="840" y="250">slot reaches only 252 / 400 = 0.63, about 63</tspan>')
    svg.append('    <tspan x="840" y="282">percent of line rate</tspan>')
    svg.append('  </text>')
    # Graphical Bar for Gen4 (width 680, height 12)
    # 252/400 = 63% fill: 680 * 0.63 = 428 px
    svg.append('  <!-- Worked Bar: Gen4 63% throughput cap -->')
    svg.append('  <rect x="840" y="291" width="680" height="8" rx="4" fill="#c4d8ca"/>')
    svg.append('  <rect x="840" y="291" width="428" height="8" rx="4" fill="#207448"/>')
    svg.append('')

    # Bar 2: PCIe Gen5 x16 (x=820, y=320, width=720, height=175)
    svg.append('  <!-- PCIe Gen5 x16 Sub-card -->')
    svg.append('  <rect x="820" y="320" width="720" height="175" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Icon: PCIe card Gen5 (56x56 at x=840, y=338)
    svg.append('  <g transform="translate(840, 338)">')
    svg.append('    <rect x="8" y="10" width="40" height="26" rx="4" fill="none" stroke="#207448" stroke-width="4"/>')
    svg.append('    <path d="M 12 36 L 12 46 M 18 36 L 18 46 M 24 36 L 24 46 M 32 36 L 32 46 M 38 36 L 38 46 M 44 36 L 44 46" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <circle cx="28" cy="23" r="6" fill="none" stroke="#207448" stroke-width="3"/>')
    svg.append('  </g>')
    # Text: PCIe Gen5 x16
    svg.append('  <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="910" y="375" font-size="30" font-weight="bold" fill="#207448">PCIe Gen5 x16: </tspan>')
    svg.append('    <tspan x="840" y="420">about 504 Gb/s, enough for a 400G port</tspan>')
    svg.append('  </text>')
    # Graphical Bar for Gen5 (width 680, height 12)
    # 504 Gb/s >= 400G port: 100% full green
    svg.append('  <!-- Worked Bar: Gen5 100% throughput full line rate -->')
    svg.append('  <rect x="840" y="445" width="680" height="8" rx="4" fill="#207448"/>')
    svg.append('')

    # --- Under it: Controller, bus, and kernel stack ---
    # Card: x=800, y=535, width=760, height=245
    svg.append('  <!-- ========================================== -->')
    svg.append('  <!-- RIGHT: Apply Method to Controller and Bus -->')
    svg.append('  <!-- ========================================== -->')
    svg.append('  <rect x="800" y="535" width="760" height="245" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('  <rect x="820" y="552" width="720" height="210" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Icon: chip / system bus (56x56 at x=840, y=567)
    svg.append('  <g transform="translate(840, 567)">')
    svg.append('    <rect x="12" y="12" width="32" height="32" rx="5" fill="none" stroke="#207448" stroke-width="4"/>')
    svg.append('    <line x1="20" y1="5" x2="20" y2="12" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <line x1="28" y1="5" x2="28" y2="12" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <line x1="36" y1="5" x2="36" y2="12" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <line x1="20" y1="44" x2="20" y2="51" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <line x1="28" y1="44" x2="28" y2="51" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <line x1="36" y1="44" x2="36" y2="51" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <circle cx="28" cy="28" r="6" fill="none" stroke="#207448" stroke-width="3"/>')
    svg.append('  </g>')
    # Text: apply the same method...
    svg.append('  <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="910" y="597" font-weight="bold">apply the same method to the NIC</tspan>')
    svg.append('    <tspan x="910" y="627" font-weight="bold">controller and the bus: </tspan>')
    svg.append('    <tspan x="840" y="663">sum the port throughputs and compare the</tspan>')
    svg.append('    <tspan x="840" y="695">total with the PCIe bandwidth; and to the</tspan>')
    svg.append('    <tspan x="840" y="727">kernel stack: softirq CPU, memory for socket</tspan>')
    svg.append('    <tspan x="840" y="759">buffers, the conntrack table</tspan>')
    svg.append('  </text>')
    svg.append('')

    # --- Lab check ---
    # Card: x=800, y=800, width=760, height=125
    svg.append('  <!-- ========================================== -->')
    svg.append('  <!-- RIGHT: Lab Check                           -->')
    svg.append('  <!-- ========================================== -->')
    svg.append('  <rect x="800" y="800" width="760" height="125" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('  <rect x="820" y="812" width="720" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Icon: checklist / report (56x56 at x=840, y=832)
    svg.append('  <g transform="translate(840, 832)">')
    svg.append('    <rect x="10" y="14" width="36" height="36" rx="4" fill="none" stroke="#207448" stroke-width="4"/>')
    svg.append('    <path d="M 20 14 V 10 C 20 8 22 6 24 6 H 32 C 34 6 36 8 36 10 V 14" fill="none" stroke="#207448" stroke-width="3"/>')
    svg.append('    <line x1="18" y1="24" x2="38" y2="24" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <line x1="18" y1="32" x2="38" y2="32" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('    <line x1="18" y1="40" x2="30" y2="40" stroke="#207448" stroke-width="3" stroke-linecap="round"/>')
    svg.append('  </g>')
    # Text: Lab check
    svg.append('  <text font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="910" y="853" font-size="30" font-weight="bold" fill="#207448">USE report for a 400G NIC: </tspan>')
    svg.append('    <tspan x="910" y="890">Gen4 x16 252 Gb/s versus Gen5 x16 504 Gb/s</tspan>')
    svg.append('  </text>')
    svg.append('')

    # --- Bottom Takeaway Bar ---
    # Bar: x=40, y=960, width=1520, height=80
    svg.append('  <!-- ========================================== -->')
    svg.append('  <!-- BOTTOM BAR: Takeaway                       -->')
    svg.append('  <!-- ========================================== -->')
    svg.append('  <rect x="40" y="960" width="1520" height="80" rx="14" fill="#207448"/>')
    svg.append('  <text x="800" y="1010" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">A slot can cap a NIC before the link does</text>')
    svg.append('</svg>')

    return '\n'.join(svg)

with open('candidate.svg', 'w') as f:
    f.write(build_svg())

print('candidate.svg written successfully.')
