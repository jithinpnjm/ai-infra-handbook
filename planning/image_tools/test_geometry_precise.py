import re
import xml.etree.ElementTree as ET

def build_candidate():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>Restarting eight replicas at once leaves a zero-capacity gap</title>')
    svg.append('  <desc>Infographic illustrating how restarting eight model replicas simultaneously causes a zero-capacity outage gap due to shared storage bandwidth saturation, compared with rolling restarts and local weight staging.</desc>')
    
    # Background
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    
    # Title (48px bold, wrapped in tspans)
    svg.append('  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Restarting eight replicas at once</tspan>')
    svg.append('    <tspan x="800" dy="54">leaves a zero-capacity gap</tspan>')
    svg.append('  </text>')
    
    # ==================== CARD 1: WORKED NUMBERS ====================
    # Box: x=50, y=138, w=1500, h=88
    svg.append('  <g id="worked-numbers">')
    svg.append('    <rect x="50" y="138" width="1500" height="88" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Icon: Storage source / rack / database with data flow (56x56 at x=75, y=154)
    svg.append('    <g transform="translate(75, 154)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="48" height="14" rx="3"/>')
    svg.append('      <line x1="12" y1="13" x2="16" y2="13"/>')
    svg.append('      <circle cx="44" cy="13" r="2" fill="#207448"/>')
    svg.append('      <rect x="4" y="24" width="48" height="14" rx="3"/>')
    svg.append('      <line x1="12" y1="31" x2="16" y2="31"/>')
    svg.append('      <circle cx="44" cy="31" r="2" fill="#207448"/>')
    svg.append('      <rect x="4" y="42" width="48" height="14" rx="3"/>')
    svg.append('      <line x1="12" y1="49" x2="16" y2="49"/>')
    svg.append('      <circle cx="44" cy="49" r="2" fill="#207448"/>')
    svg.append('    </g>')
    # Text
    svg.append('    <text x="160" y="191" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">70 billion parameters x 2 bytes = 140 GB; shared source 14 GB per second</text>')
    svg.append('  </g>')
    
    # ==================== CARD 2: TIMELINE A (ORANGE HIGHLIGHT) ====================
    # Box: x=50, y=256, w=1500, h=360
    svg.append('  <g id="timeline-a">')
    svg.append('    <rect x="50" y="256" width="1500" height="360" rx="14" fill="#fef8f2" stroke="#db8129" stroke-width="3"/>')
    # Icon: Warning / stall / zero capacity alert (56x56 at x=75, y=276)
    svg.append('    <g transform="translate(75, 276)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="28,4 52,48 4,48"/>')
    svg.append('      <line x1="28" y1="18" x2="28" y2="32"/>')
    svg.append('      <circle cx="28" cy="40" r="2" fill="#db8129"/>')
    svg.append('    </g>')
    # Text
    svg.append('    <text x="160" y="300" font-family="sans-serif" font-size="25" fill="#303a36">')
    svg.append('      <tspan x="160" dy="0">all eight restart together: 8 x 140 / 14 = 80 s each under the equal-share model,</tspan>')
    svg.append('      <tspan x="160" dy="34">endpoint has no capacity during that window;</tspan>')
    svg.append('      <tspan x="160" dy="34">retries in the gap make the first minute after recovery worse</tspan>')
    svg.append('    </text>')
    
    # Timeline A Graphical Visualization
    svg.append('    <g id="timeline-a-vis">')
    svg.append('      <rect x="160" y="394" width="1310" height="200" rx="10" fill="#ffffff" stroke="#eedcd0" stroke-width="1.5"/>')
    # Zero-capacity highlight zone
    svg.append('      <rect x="220" y="404" width="980" height="180" rx="6" fill="#fdeddc" stroke="#db8129" stroke-width="2" stroke-dasharray="6 4"/>')
    # 8 replica loading bars (all loading simultaneously across the 80s span)
    for i in range(8):
        y_bar = 416 + i * 20
        svg.append(f'      <rect x="230" y="{y_bar}" width="960" height="12" rx="3" fill="#e8b082" stroke="#db8129" stroke-width="1"/>')
    # Stalling / retry storm visual markers after gap
    svg.append('      <path d="M 1220 440 L 1245 490 L 1235 490 L 1260 550 L 1240 505 L 1250 505 Z" fill="#db8129" stroke="#db8129" stroke-width="1"/>')
    svg.append('      <path d="M 1270 430 L 1295 480 L 1285 480 L 1310 540 L 1290 495 L 1300 495 Z" fill="#db8129" stroke="#db8129" stroke-width="1"/>')
    svg.append('      <path d="M 1320 440 L 1345 490 L 1335 490 L 1360 550 L 1340 505 L 1350 505 Z" fill="#db8129" stroke="#db8129" stroke-width="1"/>')
    svg.append('    </g>')
    svg.append('  </g>')
    
    # ==================== CARD 3: TIMELINE B ====================
    # Box: x=50, y=646, w=1500, h=360
    svg.append('  <g id="timeline-b">')
    svg.append('    <rect x="50" y="646" width="1500" height="360" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    # Icon: Staged / rolling / shielded continuous serving (56x56 at x=75, y=666)
    svg.append('    <g transform="translate(75, 666)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 48 14 L 48 28 C 48 40, 28 50, 28 50 C 28 50, 8 40, 8 28 L 8 14 Z"/>')
    svg.append('      <polyline points="20,26 26,32 38,20"/>')
    svg.append('    </g>')
    # Text
    svg.append('    <text x="160" y="690" font-family="sans-serif" font-size="25" fill="#303a36">')
    svg.append('      <tspan x="160" dy="0">small groups, at least X+1 replicas keep serving;</tspan>')
    svg.append('      <tspan x="160" dy="34">weights staged on local disk so the source stops being the shared bottleneck;</tspan>')
    svg.append('      <tspan x="160" dy="34">one replica alone needs 10 s</tspan>')
    svg.append('    </text>')
    
    # Timeline B Graphical Visualization
    svg.append('    <g id="timeline-b-vis">')
    svg.append('      <rect x="160" y="784" width="1310" height="200" rx="10" fill="#ffffff" stroke="#c0d7c7" stroke-width="1.5"/>')
    
    # Replicas 1 & 2: roll in group 1 (x=230 to 450), then active serving (x=450 to 1430)
    for i in [0, 1]:
        y_bar = 796 + i * 22
        svg.append(f'      <rect x="230" y="{y_bar}" width="220" height="14" rx="3" fill="#a3d3b6" stroke="#207448" stroke-width="1"/>')
        svg.append(f'      <rect x="450" y="{y_bar}" width="980" height="14" rx="3" fill="#207448"/>')
        
    # Replicas 3 & 4: active serving (x=230 to 450), roll in group 2 (x=450 to 670), then active (x=670 to 1430)
    for i in [2, 3]:
        y_bar = 796 + i * 22
        svg.append(f'      <rect x="230" y="{y_bar}" width="220" height="14" rx="3" fill="#207448"/>')
        svg.append(f'      <rect x="450" y="{y_bar}" width="220" height="14" rx="3" fill="#a3d3b6" stroke="#207448" stroke-width="1"/>')
        svg.append(f'      <rect x="670" y="{y_bar}" width="760" height="14" rx="3" fill="#207448"/>')
        
    # Replicas 5 & 6: active serving (x=230 to 670), roll in group 3 (x=670 to 890), then active (x=890 to 1430)
    for i in [4, 5]:
        y_bar = 796 + i * 22
        svg.append(f'      <rect x="230" y="{y_bar}" width="440" height="14" rx="3" fill="#207448"/>')
        svg.append(f'      <rect x="670" y="{y_bar}" width="220" height="14" rx="3" fill="#a3d3b6" stroke="#207448" stroke-width="1"/>')
        svg.append(f'      <rect x="890" y="{y_bar}" width="540" height="14" rx="3" fill="#207448"/>')
        
    # Replicas 7 & 8: active serving (x=230 to 890), roll in group 4 (x=890 to 1110), then active (x=1110 to 1430)
    for i in [6, 7]:
        y_bar = 796 + i * 22
        svg.append(f'      <rect x="230" y="{y_bar}" width="660" height="14" rx="3" fill="#207448"/>')
        svg.append(f'      <rect x="890" y="{y_bar}" width="220" height="14" rx="3" fill="#a3d3b6" stroke="#207448" stroke-width="1"/>')
        svg.append(f'      <rect x="1110" y="{y_bar}" width="320" height="14" rx="3" fill="#207448"/>')
        
    svg.append('    </g>')
    svg.append('  </g>')
    
    # ==================== CARD 4: FOOTER TAKEAWAY BAR ====================
    # Box: x=50, y=1036, w=1500, h=136
    svg.append('  <g id="footer-takeaway">')
    svg.append('    <rect x="50" y="1036" width="1500" height="136" rx="14" fill="#207448"/>')
    # Icon: Log / terminal / inspection checklist (56x56 at x=75, y=1076)
    svg.append('    <g transform="translate(75, 1076)" stroke="#ffffff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="48" height="44" rx="6"/>')
    svg.append('      <line x1="4" y1="18" x2="52" y2="18"/>')
    svg.append('      <line x1="12" y1="28" x2="28" y2="28"/>')
    svg.append('      <line x1="12" y1="38" x2="40" y2="38"/>')
    svg.append('      <circle cx="10" cy="12" r="2" fill="#ffffff"/>')
    svg.append('      <circle cx="16" cy="12" r="2" fill="#ffffff"/>')
    svg.append('    </g>')
    # Text (white)
    svg.append('    <text x="160" y="1078" font-family="sans-serif" font-size="24" fill="#ffffff">')
    svg.append('      <tspan x="160" dy="0">measure the load time in the startup log and use that number in your answer;</tspan>')
    svg.append('      <tspan x="160" dy="32">saying you will measure first is more credible than a number you cannot defend;</tspan>')
    svg.append('      <tspan x="160" dy="32">the gap is the window to plan for, not the steady state</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return '\n'.join(svg)

svg_str = build_candidate()
with open("candidate_final.svg", "w") as f:
    f.write(svg_str)
print("Saved candidate_final.svg, bytes:", len(svg_str))
