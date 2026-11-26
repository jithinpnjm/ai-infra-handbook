import re
import xml.etree.ElementTree as ET
import asyncio
from playwright.async_api import async_playwright
import pathlib

# Let's write the complete SVG with mathematically verified paddings:
# Card width: 440 px (x = 60..500 in col 1, 580..1020 in col 2, 1100..1540 in col 3)
# Text x: card_x + 24 px (pad_left = 24 px, pad_right >= 24 px)

def generate_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>cpuset says where, quota says how much, weight says how fairly</title>')
    svg.append('  <desc>Three columns comparing cgroup CPU controls: cpuset for allowed cores, quota for hard time ceilings, and weight for fair share under contention.</desc>')
    
    # Background
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    
    # Title (48px bold, at most two lines, well inside canvas with >= 40px margin)
    # y = 88: top is at 43.0 px, bottom is at 148.0 px
    svg.append('  <text x="800" y="88" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">cpuset says where, quota says how much,</tspan>')
    svg.append('    <tspan x="800" dy="54">weight says how fairly</tspan>')
    svg.append('  </text>')

    # =========================================================================
    # COLUMN 1: cpuset (Orange on the cpuset column container)
    # x = 40, y = 175, w = 480, h = 790
    # =========================================================================
    svg.append('  <!-- ==================== COLUMN 1: cpuset ==================== -->')
    svg.append('  <g id="col-cpuset">')
    # Column 1 container (orange stroke #db8129 - exactly 1 orange occurrence)
    svg.append('    <rect x="40" y="175" width="480" height="790" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="3"/>')
    
    # Column 1 Icon: CPU chip outline (56px)
    svg.append('    <g transform="translate(60, 195)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="8" width="40" height="40" rx="6"/>')
    svg.append('      <rect x="18" y="18" width="20" height="20" rx="2" stroke-width="2.5"/>')
    svg.append('      <line x1="16" y1="2" x2="16" y2="8"/>')
    svg.append('      <line x1="28" y1="2" x2="28" y2="8"/>')
    svg.append('      <line x1="40" y1="2" x2="40" y2="8"/>')
    svg.append('      <line x1="16" y1="48" x2="16" y2="54"/>')
    svg.append('      <line x1="28" y1="48" x2="28" y2="54"/>')
    svg.append('      <line x1="40" y1="48" x2="40" y2="54"/>')
    svg.append('      <line x1="2" y1="16" x2="8" y2="16"/>')
    svg.append('      <line x1="2" y1="28" x2="8" y2="28"/>')
    svg.append('      <line x1="2" y1="40" x2="8" y2="40"/>')
    svg.append('      <line x1="48" y1="16" x2="54" y2="16"/>')
    svg.append('      <line x1="48" y1="28" x2="54" y2="28"/>')
    svg.append('      <line x1="48" y1="40" x2="54" y2="40"/>')
    svg.append('    </g>')
    
    # Column 1 Question Title (30px bold)
    svg.append('    <text x="135" y="222" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    svg.append('      <tspan x="135" dy="0">cpuset: </tspan>')
    svg.append('      <tspan x="135" dy="36">where may it run?</tspan>')
    svg.append('    </text>')

    # Item 1: File card (y = 285, h = 168)
    svg.append('    <rect x="60" y="285" width="440" height="170" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Text: top at ~306, bottom at ~436 -> pad_t = 21, pad_b = 17, pad_l = 22, pad_r = 43
    svg.append('    <text x="82" y="326" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="82" dy="0">cpuset.cpus and</tspan>')
    svg.append('      <tspan x="82" dy="26">cpuset.mems (effective</tspan>')
    svg.append('      <tspan x="82" dy="26">values in</tspan>')
    svg.append('      <tspan x="82" dy="26">cpuset.cpus.effective and</tspan>')
    svg.append('      <tspan x="82" dy="26">cpuset.mems.effective)</tspan>')
    svg.append('    </text>')

    # Item 2: Picture card - CPUs 4 to 7 highlighted out of 0 to 7 (y = 465, h = 76)
    svg.append('    <rect x="60" y="470" width="440" height="75" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <!-- Visual CPU cores: 0 to 3 idle/outline, 4 to 7 highlighted/filled -->')
    svg.append('    <g transform="translate(76, 478)">')
    for i in range(8):
        cx = i * 50
        if i < 4:
            # Idle cores 0 to 3
            svg.append(f'      <g transform="translate({cx}, 0)">')
            svg.append('        <rect x="0" y="5" width="38" height="40" rx="4" fill="#f5f8f5" stroke="#207448" stroke-width="1.5"/>')
            svg.append('        <rect x="11" y="16" width="16" height="18" rx="2" fill="none" stroke="#207448" stroke-width="1"/>')
            svg.append('        <line x1="10" y1="1" x2="10" y2="5" stroke="#207448" stroke-width="1.5"/>')
            svg.append('        <line x1="19" y1="1" x2="19" y2="5" stroke="#207448" stroke-width="1.5"/>')
            svg.append('        <line x1="28" y1="1" x2="28" y2="5" stroke="#207448" stroke-width="1.5"/>')
            svg.append('        <line x1="10" y1="45" x2="10" y2="49" stroke="#207448" stroke-width="1.5"/>')
            svg.append('        <line x1="19" y1="45" x2="19" y2="49" stroke="#207448" stroke-width="1.5"/>')
            svg.append('        <line x1="28" y1="45" x2="28" y2="49" stroke="#207448" stroke-width="1.5"/>')
            svg.append('      </g>')
        else:
            # Highlighted cores 4 to 7
            svg.append(f'      <g transform="translate({cx}, 0)">')
            svg.append('        <rect x="0" y="5" width="38" height="40" rx="4" fill="#207448" stroke="#207448" stroke-width="2"/>')
            svg.append('        <rect x="11" y="16" width="16" height="18" rx="2" fill="#ffffff" stroke="none"/>')
            svg.append('        <line x1="10" y1="1" x2="10" y2="5" stroke="#207448" stroke-width="2"/>')
            svg.append('        <line x1="19" y1="1" x2="19" y2="5" stroke="#207448" stroke-width="2"/>')
            svg.append('        <line x1="28" y1="1" x2="28" y2="5" stroke="#207448" stroke-width="2"/>')
            svg.append('        <line x1="10" y1="45" x2="10" y2="49" stroke="#207448" stroke-width="2"/>')
            svg.append('        <line x1="19" y1="45" x2="19" y2="49" stroke="#207448" stroke-width="2"/>')
            svg.append('        <line x1="28" y1="45" x2="28" y2="49" stroke="#207448" stroke-width="2"/>')
            svg.append('      </g>')
    svg.append('    </g>')

    # Item 3: Note card (y = 553, h = 150)
    svg.append('    <rect x="60" y="553" width="440" height="150" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Text: top at ~574, bottom at ~684 -> pad_t = 21, pad_b = 19, pad_l = 22
    svg.append('    <text x="82" y="594" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="82" dy="0">a hard allow-list, no</tspan>')
    svg.append('      <tspan x="82" dy="28">throttling; an empty</tspan>')
    svg.append('      <tspan x="82" dy="28">cpuset.cpus inherits</tspan>')
    svg.append('      <tspan x="82" dy="28">the parent\'s</tspan>')
    svg.append('    </text>')

    # Item 4: Use card (y = 715, h = 232)
    svg.append('    <rect x="60" y="715" width="440" height="232" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Text: top at ~738, bottom at ~914 -> pad_t = 23, pad_b = 33, pad_l = 22
    svg.append('    <text x="82" y="758" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="82" dy="0">a job that must run on</tspan>')
    svg.append('      <tspan x="82" dy="30">cores 4 to 7; Slurm</tspan>')
    svg.append('      <tspan x="82" dy="30">task/cgroup and the</tspan>')
    svg.append('      <tspan x="82" dy="30">Kubernetes CPU Manager</tspan>')
    svg.append('      <tspan x="82" dy="30">use cpusets for exclusive</tspan>')
    svg.append('      <tspan x="82" dy="30">cores</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # =========================================================================
    # COLUMN 2: quota (cpu.max)
    # x = 560, y = 175, w = 480, h = 790
    # =========================================================================
    svg.append('  <!-- ==================== COLUMN 2: quota ==================== -->')
    svg.append('  <g id="col-quota">')
    svg.append('    <rect x="560" y="175" width="480" height="790" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')

    # Column 2 Icon: Gauge / Timer outline (56px)
    svg.append('    <g transform="translate(580, 195)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 8 46 A 22 22 0 1 1 48 46"/>')
    svg.append('      <line x1="28" y1="28" x2="40" y2="16" stroke-width="3.5"/>')
    svg.append('      <circle cx="28" cy="28" r="4" fill="#207448"/>')
    svg.append('      <line x1="10" y1="46" x2="46" y2="46" stroke-width="2.5"/>')
    svg.append('    </g>')

    # Column 2 Question Title (30px bold)
    svg.append('    <text x="655" y="222" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    svg.append('      <tspan x="655" dy="0">quota (cpu.max): </tspan>')
    svg.append('      <tspan x="655" dy="36">how much time?</tspan>')
    svg.append('    </text>')

    # Item 1: File card (y = 285, h = 168)
    svg.append('    <rect x="580" y="285" width="440" height="170" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Text: top at ~312, bottom at ~422 -> pad_t = 27, pad_b = 31, pad_l = 22
    svg.append('    <text x="602" y="332" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="602" dy="0">cpu.max = $MAX $PERIOD</tspan>')
    svg.append('      <tspan x="602" dy="28">in microseconds</tspan>')
    svg.append('      <tspan x="602" dy="28">(200000 100000 =</tspan>')
    svg.append('      <tspan x="602" dy="28">2 CPUs worth)</tspan>')
    svg.append('    </text>')

    # Item 2: Picture card - a fuel gauge that empties mid-period (y = 465, h = 160)
    svg.append('    <rect x="580" y="470" width="440" height="155" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <!-- Visual fuel gauge and timeline emptying mid-period -->')
    svg.append('    <g transform="translate(600, 480)">')
    # Dial gauge on left
    svg.append('      <g transform="translate(15, 12)">')
    svg.append('        <path d="M 10 65 A 38 38 0 1 1 74 65" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round"/>')
    svg.append('        <line x1="14" y1="60" x2="22" y2="54" stroke="#207448" stroke-width="2.5"/>')
    svg.append('        <line x1="42" y1="14" x2="42" y2="23" stroke="#207448" stroke-width="2.5"/>')
    svg.append('        <line x1="70" y1="60" x2="62" y2="54" stroke="#207448" stroke-width="2.5"/>')
    svg.append('        <line x1="42" y1="50" x2="18" y2="58" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>')
    svg.append('        <circle cx="42" cy="50" r="5" fill="#207448"/>')
    svg.append('      </g>')
    # Horizontal timeline progress bar
    svg.append('      <g transform="translate(125, 36)">')
    svg.append('        <rect x="0" y="0" width="250" height="36" rx="6" fill="#f5f8f5" stroke="#207448" stroke-width="2"/>')
    svg.append('        <rect x="0" y="0" width="100" height="36" rx="6" fill="#207448"/>')
    svg.append('        <line x1="100" y1="-8" x2="100" y2="44" stroke="#207448" stroke-width="2.5" stroke-dasharray="3,3"/>')
    svg.append('        <line x1="125" y1="5" x2="145" y2="31" stroke="#a9c4b3" stroke-width="2"/>')
    svg.append('        <line x1="155" y1="5" x2="175" y2="31" stroke="#a9c4b3" stroke-width="2"/>')
    svg.append('        <line x1="185" y1="5" x2="205" y2="31" stroke="#a9c4b3" stroke-width="2"/>')
    svg.append('        <line x1="215" y1="5" x2="235" y2="31" stroke="#a9c4b3" stroke-width="2"/>')
    svg.append('      </g>')
    svg.append('    </g>')

    # Item 3: Use card (y = 637, h = 310)
    svg.append('    <rect x="580" y="637" width="440" height="310" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Text: top at ~735, bottom at ~835 -> pad_t = 98, pad_b = 112, pad_l = 22
    svg.append('    <text x="602" y="756" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="602" dy="0">a job that may run on any</tspan>')
    svg.append('      <tspan x="602" dy="36">cores as long as it gets</tspan>')
    svg.append('      <tspan x="602" dy="36">4 CPUs worth of time</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # =========================================================================
    # COLUMN 3: weight (cpu.weight)
    # x = 1080, y = 175, w = 480, h = 790
    # =========================================================================
    svg.append('  <!-- ==================== COLUMN 3: weight ==================== -->')
    svg.append('  <g id="col-weight">')
    svg.append('    <rect x="1080" y="175" width="480" height="790" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')

    # Column 3 Icon: Balance scale outline (56px)
    svg.append('    <g transform="translate(1100, 195)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="28" y1="8" x2="28" y2="48"/>')
    svg.append('      <line x1="10" y1="18" x2="46" y2="18"/>')
    svg.append('      <line x1="14" y1="48" x2="42" y2="48"/>')
    svg.append('      <polyline points="10,18 4,32 16,32 10,18"/>')
    svg.append('      <polyline points="46,18 40,32 52,32 46,18"/>')
    svg.append('    </g>')

    # Column 3 Question Title (30px bold, 3 lines)
    svg.append('    <text x="1175" y="222" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">')
    svg.append('      <tspan x="1175" dy="0">weight (cpu.weight): </tspan>')
    svg.append('      <tspan x="1175" dy="32">how fairly under</tspan>')
    svg.append('      <tspan x="1175" dy="32">contention?</tspan>')
    svg.append('    </text>')

    # Item 1: File card (y = 285, h = 168)
    svg.append('    <rect x="1100" y="285" width="440" height="170" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Text: top at ~330, bottom at ~418 -> pad_t = 45, pad_b = 35, pad_l = 22
    svg.append('    <text x="1122" y="338" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1122" dy="0">cpu.weight 1 to 10000,</tspan>')
    svg.append('      <tspan x="1122" dy="30">default 100; v1</tspan>')
    svg.append('      <tspan x="1122" dy="30">cpu.shares default 1024</tspan>')
    svg.append('    </text>')

    # Item 2: Picture card - two sibling bars 100 and 300 splitting 25% and 75% (y = 465, h = 160)
    svg.append('    <rect x="1100" y="470" width="440" height="155" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    svg.append('    <!-- Visual two sibling bars 100 and 300 splitting 25% and 75% -->')
    svg.append('    <g transform="translate(1125, 485)">')
    # Sibling Bar A
    svg.append('      <g transform="translate(5, 10)">')
    svg.append('        <rect x="0" y="0" width="95" height="38" rx="6" fill="#a9c4b3" stroke="#207448" stroke-width="2"/>')
    svg.append('        <line x1="95" y1="0" x2="380" y2="0" stroke="#e8f1ea" stroke-width="2" stroke-dasharray="4,4"/>')
    svg.append('        <line x1="95" y1="38" x2="380" y2="38" stroke="#e8f1ea" stroke-width="2" stroke-dasharray="4,4"/>')
    svg.append('        <line x1="380" y1="0" x2="380" y2="38" stroke="#e8f1ea" stroke-width="2"/>')
    svg.append('      </g>')
    # Sibling Bar B
    svg.append('      <g transform="translate(5, 65)">')
    svg.append('        <rect x="0" y="0" width="285" height="38" rx="6" fill="#207448" stroke="#207448" stroke-width="2"/>')
    svg.append('        <line x1="285" y1="0" x2="380" y2="0" stroke="#e8f1ea" stroke-width="2" stroke-dasharray="4,4"/>')
    svg.append('        <line x1="285" y1="38" x2="380" y2="38" stroke="#e8f1ea" stroke-width="2" stroke-dasharray="4,4"/>')
    svg.append('        <line x1="380" y1="0" x2="380" y2="38" stroke="#e8f1ea" stroke-width="2"/>')
    svg.append('      </g>')
    svg.append('    </g>')

    # Item 3: Note card (y = 637, h = 310)
    svg.append('    <rect x="1100" y="637" width="440" height="310" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Text: top at ~666, bottom at ~864 -> pad_t = 29, pad_b = 83, pad_l = 22
    svg.append('    <text x="1122" y="688" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1122" dy="0">invisible on an idle</tspan>')
    svg.append('      <tspan x="1122" dy="34">machine, never wastes</tspan>')
    svg.append('      <tspan x="1122" dy="34">capacity, never limits</tspan>')
    svg.append('      <tspan x="1122" dy="34">alone; Kubernetes CPU</tspan>')
    svg.append('      <tspan x="1122" dy="34">request becomes shares</tspan>')
    svg.append('      <tspan x="1122" dy="34">or weight</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # =========================================================================
    # BOTTOM STRIP: v2 partitions
    # x = 40, y = 985, w = 1520, h = 95
    # =========================================================================
    svg.append('  <!-- ==================== BOTTOM STRIP ==================== -->')
    svg.append('  <g id="bottom-strip">')
    svg.append('    <rect x="40" y="980" width="1520" height="100" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Small Chip / Partition Outline Icon
    svg.append('    <g transform="translate(60, 1005)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="44" height="42" rx="4"/>')
    svg.append('      <line x1="26" y1="6" x2="26" y2="48" stroke-dasharray="3,3"/>')
    svg.append('      <rect x="10" y="16" width="10" height="12" rx="2" fill="#207448"/>')
    svg.append('    </g>')
    # Text: top at ~1008, bottom at ~1068 -> pad_t = 23, pad_b = 27, pad_l = 90
    svg.append('    <text x="130" y="1024" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="130" dy="0">v2 partitions: cpuset.cpus.partition set to root or isolated makes a group with exclusive</tspan>')
    svg.append('      <tspan x="130" dy="32">CPUs, a runtime alternative to isolcpus</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # =========================================================================
    # BOTTOM BAR (Takeaway bar): Choose placement, ceiling or proportion
    # x = 40, y = 1100, w = 1520, h = 60
    # =========================================================================
    svg.append('  <!-- ==================== BOTTOM BAR ==================== -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1094" width="1520" height="66" rx="10" fill="#207448"/>')
    # Text: top at 1115, bottom at 1145 -> pad_t = 15, pad_b = 15
    svg.append('    <text x="800" y="1137" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Choose placement, ceiling or proportion by what the job needs</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

with open("test_candidate_cpuset.svg", "w") as f:
    f.write(generate_svg())
print("Wrote solved test_candidate_cpuset.svg")

