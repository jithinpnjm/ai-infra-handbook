import re
import xml.etree.ElementTree as ET

def generate_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200" role="img">')
    svg.append('  <title>Where did my RAM go: reading free and /proc/meminfo</title>')
    svg.append('  <desc>Visual explanation of Linux free command output, MemAvailable, and RAM breakdown from /proc/meminfo.</desc>')
    
    # Background
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    
    # Title (48px bold, max 2 lines, well inside canvas)
    svg.append('  <text x="800" y="60" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Where did my RAM go:</tspan>')
    svg.append('    <tspan x="800" dy="54">reading free and /proc/meminfo</tspan>')
    svg.append('  </text>')
    
    # Terminal output box
    # x=40, y=140, w=1520, h=100, rx=12
    svg.append('  <!-- Terminal output box -->')
    svg.append('  <rect x="40" y="140" width="1520" height="100" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('  <circle cx="65" cy="162" r="6" fill="#207448" opacity="0.3"/>')
    svg.append('  <circle cx="85" cy="162" r="6" fill="#207448" opacity="0.3"/>')
    svg.append('  <circle cx="105" cy="162" r="6" fill="#207448" opacity="0.3"/>')
    
    # Monospace Line 1:
    svg.append('  <text x="135" y="188" font-family="monospace" font-size="24" font-weight="bold" fill="#207448" xml:space="preserve">total 1.9Ti  used 120Gi  free 40Gi  shared 1.2Gi  buff/cache 1.7Ti  available 1.7Ti</text>')
    
    # Monospace Line 2: Swap line '0B 0B 0B'
    svg.append('  <text x="135" y="222" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">0B 0B 0B</text>')
    
    # Middle Top: Two Annotation Cards (free & available)
    # y=265 to 445 (h=180)
    # Card A (free): x=40 to 780 (w=740)
    # Card B (available): x=820 to 1560 (w=740)
    
    # Card A: free
    svg.append('  <!-- Card: free -->')
    svg.append('  <rect x="40" y="265" width="740" height="180" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Gauge/Clock outline icon (56x56, green stroke 4)
    svg.append('  <g transform="translate(68, 327)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="28" cy="28" r="24"/>')
    svg.append('    <line x1="28" y1="28" x2="28" y2="14"/>')
    svg.append('    <line x1="28" y1="28" x2="38" y2="28"/>')
    svg.append('  </g>')
    # Title: 'free'
    svg.append('  <text x="150" y="325" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">free</text>')
    # Note: 'idle memory, deliberately small'
    svg.append('  <text x="150" y="375" font-family="sans-serif" font-size="24" fill="#303a36">idle memory, deliberately small</text>')
    
    # Card B: available
    svg.append('  <!-- Card: available -->')
    svg.append('  <rect x="820" y="265" width="740" height="180" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Application / Window outline icon (56x56, green stroke 4)
    svg.append('  <g transform="translate(848, 327)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="6" width="48" height="44" rx="4"/>')
    svg.append('    <line x1="4" y1="18" x2="52" y2="18"/>')
    svg.append('    <circle cx="12" cy="12" r="2" fill="#207448"/>')
    svg.append('    <circle cx="18" cy="12" r="2" fill="#207448"/>')
    svg.append('  </g>')
    
    # 'available' circled in orange
    # Pill around 'available':
    svg.append('  <rect x="922" y="283" width="160" height="42" rx="21" fill="none" stroke="#db8129" stroke-width="3"/>')
    svg.append('  <text x="942" y="313" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">available</text>')
    
    # Note: 'MemAvailable: how much you can use to start new applications without swapping; counts reclaimable page cache and slab'
    # Wrapped onto 3 lines
    svg.append('  <text x="926" y="352" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="926" dy="0">MemAvailable: how much you can use to start</tspan>')
    svg.append('    <tspan x="926" dy="28">new applications without swapping; counts</tspan>')
    svg.append('    <tspan x="926" dy="28">reclaimable page cache and slab</tspan>')
    svg.append('  </text>')
    
    # Bottom Section: Stacked Bar of RAM + Side Box
    # y=475 to 1065 (h=590)
    # Stacked bar on left: x=40 to 1030 (w=990)
    # Side box on right: x=1070 to 1560 (w=490)
    
    # Stacked bar container
    svg.append('  <!-- Stacked Bar of RAM Container -->')
    svg.append('  <rect x="40" y="475" width="990" height="590" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    
    # 6 segments:
    # h_seg = 86, gap = 8 -> 6 * 86 + 5 * 8 = 516 + 40 = 556. Top pad = 17, bot pad = 17.
    # y0 = 475 + 17 = 492.
    
    segments_data = [
        ("AnonPages: process private heap and stack", False, "heap"),
        ("Cached: page cache, including mapped files and tmpfs through Shmem", True, "disk"),
        ("Slab = SReclaimable (can be freed) + SUnreclaim (cannot)", False, "gear"),
        ("PageTables and KernelStack: kernel overhead", False, "chip"),
        ("HugePages_*: explicitly reserved, ordinary allocation cannot use it", True, "layer"),
        ("Mlocked and Unevictable: reclaim cannot touch", False, "lock")
    ]
    
    def render_icon(name, ix, iy):
        if name == "heap":
            return f'''<g transform="translate({ix}, {iy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <polygon points="28,8 48,18 28,28 8,18"/>
              <polyline points="8,26 28,36 48,26"/>
              <polyline points="8,34 28,44 48,34"/>
            </g>'''
        elif name == "disk":
            return f'''<g transform="translate({ix}, {iy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <ellipse cx="28" cy="14" rx="20" ry="8"/>
              <path d="M8,14 v22 c0,4.4 9,8 20,8 s20,-3.6 20,-8 v-22"/>
              <path d="M8,25 c0,4.4 9,8 20,8 s20,-3.6 20,-8"/>
            </g>'''
        elif name == "gear":
            return f'''<g transform="translate({ix}, {iy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <circle cx="28" cy="28" r="10"/>
              <path d="M28,6 v6 M28,44 v6 M6,28 h6 M44,28 h6 M12,12 l5,5 M39,39 l5,5 M12,44 l5,-5 M39,17 l5,-5"/>
            </g>'''
        elif name == "chip":
            return f'''<g transform="translate({ix}, {iy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <rect x="12" y="12" width="32" height="32" rx="4"/>
              <line x1="20" y1="4" x2="20" y2="12"/><line x1="28" y1="4" x2="28" y2="12"/><line x1="36" y1="4" x2="36" y2="12"/>
              <line x1="20" y1="44" x2="20" y2="52"/><line x1="28" y1="44" x2="28" y2="52"/><line x1="36" y1="44" x2="36" y2="52"/>
              <line x1="4" y1="20" x2="12" y2="20"/><line x1="4" y1="28" x2="12" y2="28"/><line x1="4" y1="36" x2="12" y2="36"/>
              <line x1="44" y1="20" x2="52" y2="20"/><line x1="44" y1="28" x2="52" y2="28"/><line x1="44" y1="36" x2="52" y2="36"/>
            </g>'''
        elif name == "layer":
            return f'''<g transform="translate({ix}, {iy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <rect x="8" y="8" width="40" height="40" rx="4"/>
              <line x1="8" y1="28" x2="48" y2="28"/>
              <line x1="28" y1="8" x2="28" y2="48"/>
            </g>'''
        elif name == "lock":
            return f'''<g transform="translate({ix}, {iy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
              <rect x="10" y="22" width="36" height="26" rx="4"/>
              <path d="M18,22 v-8 a10,10 0 0,1 20,0 v8"/>
              <circle cx="28" cy="35" r="3" fill="#207448"/>
            </g>'''
    
    cur_y = 492
    for label, is_two_line, icon_type in segments_data:
        svg.append(f'  <rect x="56" y="{cur_y}" width="958" height="86" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
        svg.append(f'  <path d="M 56 {cur_y+10} A 10 10 0 0 1 66 {cur_y} L 76 {cur_y} L 76 {cur_y+86} L 66 {cur_y+86} A 10 10 0 0 1 56 {cur_y+76} Z" fill="#207448"/>')
        
        svg.append(render_icon(icon_type, 90, cur_y + 15))
        
        tx = 166
        if is_two_line:
            if "Cached" in label:
                svg.append(f'  <text x="{tx}" y="{cur_y + 38}" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
                svg.append(f'    <tspan x="{tx}" dy="0">Cached: page cache, including mapped files</tspan>')
                svg.append(f'    <tspan x="{tx}" dy="28">and tmpfs through Shmem</tspan>')
                svg.append('  </text>')
            elif "HugePages" in label:
                svg.append(f'  <text x="{tx}" y="{cur_y + 38}" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
                svg.append(f'    <tspan x="{tx}" dy="0">HugePages_*: explicitly reserved,</tspan>')
                svg.append(f'    <tspan x="{tx}" dy="28">ordinary allocation cannot use it</tspan>')
                svg.append('  </text>')
        else:
            svg.append(f'  <text x="{tx}" y="{cur_y + 51}" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">{label}</text>')
            
        cur_y += 94
        
    # Side Box
    # x=1070 to 1560 (w=490, y=475 to 1065, h=590)
    svg.append('  <!-- Side Box -->')
    svg.append('  <rect x="1070" y="475" width="490" height="590" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('  <g transform="translate(1287, 660)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M28,6 L48,16 V32 C48,44 28,52 28,52 C28,52 8,44 8,32 V16 Z"/>')
    svg.append('    <line x1="28" y1="20" x2="28" y2="34"/>')
    svg.append('    <circle cx="28" cy="40" r="2" fill="#207448"/>')
    svg.append('  </g>')
    # Side box text
    svg.append('  <text x="1315" y="770" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="1315" dy="0">In buff/cache, shared and</tspan>')
    svg.append('    <tspan x="1315" dy="36">tmpfs pages and mlocked</tspan>')
    svg.append('    <tspan x="1315" dy="36">pages are not reclaimable</tspan>')
    svg.append('  </text>')
    
    # Bottom bar: 'Read available, not free'
    # x=40, y=1095, w=1520, h=65, rx=12
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <rect x="40" y="1095" width="1520" height="65" rx="12" fill="#207448"/>')
    svg.append('  <text x="800" y="1136" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Read available, not free</text>')
    
    svg.append('</svg>')
    return "\n".join(svg)

content = generate_svg()
with open("test_candidate_meminfo.svg", "w") as f:
    f.write(content)
print("Updated test_candidate_meminfo.svg")
