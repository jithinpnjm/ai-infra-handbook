import re
import xml.etree.ElementTree as ET

def generate_svg():
    W = 1600
    H = 1020
    
    # Palette
    BG = "#f5f8f5"
    TEXT = "#303a36"
    MAIN_GREEN = "#207448"
    LIGHT_GREEN = "#e8f1ea"
    ORANGE = "#db8129"
    WHITE = "#ffffff"
    
    # Coordinates
    # Top title: y = 68
    # Cards: 4 columns
    # x: 40, 431, 822, 1214; w = 345
    card_w = 345
    card_h = 490
    card_y = 125
    xs = [40, 431, 822, 1214]
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>A four-week practice routine</title>')
    svg.append('  <desc>A horizontal timeline of four week blocks showing focus, session time, end-of-week test milestones, bug log tracking, and timed practice routine.</desc>')
    svg.append('')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append(f'      <path d="M 2 3 L 16 9 L 2 15 Z" fill="{MAIN_GREEN}" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    svg.append('')
    svg.append(f'  <!-- Background -->')
    svg.append(f'  <rect width="{W}" height="{H}" fill="{BG}" />')
    svg.append('')
    svg.append(f'  <!-- Title (48px bold) -->')
    svg.append(f'  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="{TEXT}">A four-week practice routine</text>')
    svg.append('')
    
    # Helper to build card header and outline
    # Week 1
    x1 = xs[0]
    svg.append('  <!-- ==================== WEEK 1 CARD ==================== -->')
    svg.append(f'  <g id="card-week-1">')
    svg.append(f'    <rect x="{x1}" y="{card_y}" width="{card_w}" height="{card_h}" rx="16" fill="{WHITE}" stroke="{MAIN_GREEN}" stroke-width="2.5" />')
    # Green header
    svg.append(f'    <path d="M {x1} {card_y+16} A 16 16 0 0 1 {x1+16} {card_y} H {x1+card_w-16} A 16 16 0 0 1 {x1+card_w} {card_y+16} V {card_y+130} H {x1} Z" fill="{MAIN_GREEN}" />')
    # Number circle 1
    svg.append(f'    <circle cx="{x1+48}" cy="{card_y+42}" r="24" fill="{WHITE}" />')
    svg.append(f'    <text x="{x1+48}" y="{card_y+51}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{MAIN_GREEN}">1</text>')
    # Outline icon 1: terminal / code window (56x56)
    svg.append(f'    <g transform="translate({x1+card_w-76}, {card_y+14})">')
    svg.append(f'      <rect x="4" y="6" width="48" height="44" rx="6" fill="none" stroke="{WHITE}" stroke-width="3.5" />')
    svg.append(f'      <line x1="4" y1="18" x2="52" y2="18" stroke="{WHITE}" stroke-width="2.5" />')
    svg.append(f'      <polyline points="12,28 20,34 12,40" fill="none" stroke="{WHITE}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')
    svg.append(f'      <line x1="24" y1="40" x2="36" y2="40" stroke="{WHITE}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'    </g>')
    # Title: Language basics
    svg.append(f'    <text x="{x1+card_w//2}" y="{card_y+108}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{WHITE}">Language basics</text>')
    # Topic panel: Dicts, counters, sorting, strings, the harness
    svg.append(f'    <rect x="{x1+15}" y="{card_y+150}" width="315" height="195" rx="12" fill="{LIGHT_GREEN}" />')
    svg.append(f'    <text x="{x1+card_w//2}" y="{card_y+210}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{TEXT}">')
    svg.append(f'      <tspan x="{x1+card_w//2}" dy="0">Dicts, counters, </tspan>')
    svg.append(f'      <tspan x="{x1+card_w//2}" dy="36">sorting, strings, </tspan>')
    svg.append(f'      <tspan x="{x1+card_w//2}" dy="36">the harness</tspan>')
    svg.append(f'    </text>')
    # Time panel: Time: 5 sessions of 1 hour
    svg.append(f'    <rect x="{x1+15}" y="{card_y+365}" width="315" height="105" rx="12" fill="{BG}" stroke="{MAIN_GREEN}" stroke-width="2" />')
    svg.append(f'    <text x="{x1+card_w//2}" y="{card_y+412}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{MAIN_GREEN}">')
    svg.append(f'      <tspan x="{x1+card_w//2}" dy="0">Time: 5 sessions </tspan>')
    svg.append(f'      <tspan x="{x1+card_w//2}" dy="34">of 1 hour</tspan>')
    svg.append(f'    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Week 2
    x2 = xs[1]
    svg.append('  <!-- ==================== WEEK 2 CARD ==================== -->')
    svg.append(f'  <g id="card-week-2">')
    svg.append(f'    <rect x="{x2}" y="{card_y}" width="{card_w}" height="{card_h}" rx="16" fill="{WHITE}" stroke="{MAIN_GREEN}" stroke-width="2.5" />')
    # Green header
    svg.append(f'    <path d="M {x2} {card_y+16} A 16 16 0 0 1 {x2+16} {card_y} H {x2+card_w-16} A 16 16 0 0 1 {x2+card_w} {card_y+16} V {card_y+130} H {x2} Z" fill="{MAIN_GREEN}" />')
    # Number circle 2
    svg.append(f'    <circle cx="{x2+48}" cy="{card_y+42}" r="24" fill="{WHITE}" />')
    svg.append(f'    <text x="{x2+48}" y="{card_y+51}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{MAIN_GREEN}">2</text>')
    # Outline icon 2: pattern blocks / grid (56x56)
    svg.append(f'    <g transform="translate({x2+card_w-76}, {card_y+14})">')
    svg.append(f'      <rect x="6" y="8" width="18" height="18" rx="4" fill="none" stroke="{WHITE}" stroke-width="3" />')
    svg.append(f'      <rect x="32" y="8" width="18" height="18" rx="4" fill="none" stroke="{WHITE}" stroke-width="3" />')
    svg.append(f'      <rect x="6" y="34" width="18" height="18" rx="4" fill="none" stroke="{WHITE}" stroke-width="3" />')
    svg.append(f'      <rect x="32" y="34" width="18" height="18" rx="4" fill="none" stroke="{WHITE}" stroke-width="3" />')
    svg.append(f'    </g>')
    # Title: Core patterns
    svg.append(f'    <text x="{x2+card_w//2}" y="{card_y+108}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{WHITE}">Core patterns</text>')
    # Topic panel: Hash maps, two pointers, sliding window, stacks
    svg.append(f'    <rect x="{x2+15}" y="{card_y+150}" width="315" height="195" rx="12" fill="{LIGHT_GREEN}" />')
    svg.append(f'    <text x="{x2+card_w//2}" y="{card_y+198}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{TEXT}">')
    svg.append(f'      <tspan x="{x2+card_w//2}" dy="0">Hash maps, </tspan>')
    svg.append(f'      <tspan x="{x2+card_w//2}" dy="32">two pointers, </tspan>')
    svg.append(f'      <tspan x="{x2+card_w//2}" dy="32">sliding window, </tspan>')
    svg.append(f'      <tspan x="{x2+card_w//2}" dy="32">stacks</tspan>')
    svg.append(f'    </text>')
    # Time panel: Time: 4 sessions of 75 minutes
    svg.append(f'    <rect x="{x2+15}" y="{card_y+365}" width="315" height="105" rx="12" fill="{BG}" stroke="{MAIN_GREEN}" stroke-width="2" />')
    svg.append(f'    <text x="{x2+card_w//2}" y="{card_y+412}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{MAIN_GREEN}">')
    svg.append(f'      <tspan x="{x2+card_w//2}" dy="0">Time: 4 sessions </tspan>')
    svg.append(f'      <tspan x="{x2+card_w//2}" dy="34">of 75 minutes</tspan>')
    svg.append(f'    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Week 3
    x3 = xs[2]
    svg.append('  <!-- ==================== WEEK 3 CARD ==================== -->')
    svg.append(f'  <g id="card-week-3">')
    svg.append(f'    <rect x="{x3}" y="{card_y}" width="{card_w}" height="{card_h}" rx="16" fill="{WHITE}" stroke="{MAIN_GREEN}" stroke-width="2.5" />')
    # Green header
    svg.append(f'    <path d="M {x3} {card_y+16} A 16 16 0 0 1 {x3+16} {card_y} H {x3+card_w-16} A 16 16 0 0 1 {x3+card_w} {card_y+16} V {card_y+130} H {x3} Z" fill="{MAIN_GREEN}" />')
    # Number circle 3
    svg.append(f'    <circle cx="{x3+48}" cy="{card_y+42}" r="24" fill="{WHITE}" />')
    svg.append(f'    <text x="{x3+48}" y="{card_y+51}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{MAIN_GREEN}">3</text>')
    # Outline icon 3: tree / graph / heap (56x56)
    svg.append(f'    <g transform="translate({x3+card_w-76}, {card_y+14})">')
    svg.append(f'      <circle cx="28" cy="12" r="7" fill="none" stroke="{WHITE}" stroke-width="3" />')
    svg.append(f'      <circle cx="14" cy="42" r="7" fill="none" stroke="{WHITE}" stroke-width="3" />')
    svg.append(f'      <circle cx="42" cy="42" r="7" fill="none" stroke="{WHITE}" stroke-width="3" />')
    svg.append(f'      <line x1="23" y1="18" x2="17" y2="36" stroke="{WHITE}" stroke-width="2.5" />')
    svg.append(f'      <line x1="33" y1="18" x2="39" y2="36" stroke="{WHITE}" stroke-width="2.5" />')
    svg.append(f'    </g>')
    # Header decoration / badge: Heaps, intervals, binary search, graphs is the main label
    # In header, we can place a subtitle style or icon flourish, but remember: NO NEW WORDS!
    # So header has the number circle and icon prominently.
    # Topic panel: Heaps, intervals, binary search, graphs
    svg.append(f'    <rect x="{x3+15}" y="{card_y+150}" width="315" height="195" rx="12" fill="{LIGHT_GREEN}" />')
    svg.append(f'    <text x="{x3+card_w//2}" y="{card_y+210}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{TEXT}">')
    svg.append(f'      <tspan x="{x3+card_w//2}" dy="0">Heaps, intervals, </tspan>')
    svg.append(f'      <tspan x="{x3+card_w//2}" dy="36">binary search, </tspan>')
    svg.append(f'      <tspan x="{x3+card_w//2}" dy="36">graphs</tspan>')
    svg.append(f'    </text>')
    # Time panel: Time: 4 sessions of 75 minutes
    svg.append(f'    <rect x="{x3+15}" y="{card_y+365}" width="315" height="105" rx="12" fill="{BG}" stroke="{MAIN_GREEN}" stroke-width="2" />')
    svg.append(f'    <text x="{x3+card_w//2}" y="{card_y+412}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{MAIN_GREEN}">')
    svg.append(f'      <tspan x="{x3+card_w//2}" dy="0">Time: 4 sessions </tspan>')
    svg.append(f'      <tspan x="{x3+card_w//2}" dy="34">of 75 minutes</tspan>')
    svg.append(f'    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Week 4 (Orange outline on Week 4 card!)
    x4 = xs[3]
    svg.append('  <!-- ==================== WEEK 4 CARD ==================== -->')
    svg.append(f'  <g id="card-week-4">')
    # Orange outline on Week 4 card!
    svg.append(f'    <rect x="{x4}" y="{card_y}" width="{card_w}" height="{card_h}" rx="16" fill="{WHITE}" stroke="{ORANGE}" stroke-width="4" />')
    # Green header
    svg.append(f'    <path d="M {x4} {card_y+16} A 16 16 0 0 1 {x4+16} {card_y} H {x4+card_w-16} A 16 16 0 0 1 {x4+card_w} {card_y+16} V {card_y+130} H {x4} Z" fill="{MAIN_GREEN}" />')
    # Number circle 4
    svg.append(f'    <circle cx="{x4+48}" cy="{card_y+42}" r="24" fill="{WHITE}" />')
    svg.append(f'    <text x="{x4+48}" y="{card_y+51}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{MAIN_GREEN}">4</text>')
    # Outline icon 4: stopwatch / clock (56x56)
    svg.append(f'    <g transform="translate({x4+card_w-76}, {card_y+14})">')
    svg.append(f'      <circle cx="28" cy="30" r="21" fill="none" stroke="{WHITE}" stroke-width="3.5" />')
    svg.append(f'      <line x1="28" y1="16" x2="28" y2="30" stroke="{WHITE}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'      <line x1="28" y1="30" x2="38" y2="30" stroke="{WHITE}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'      <line x1="28" y1="2" x2="28" y2="8" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" />')
    svg.append(f'      <path d="M 40 10 L 46 16" stroke="{WHITE}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'    </g>')
    # Title: Full mock rounds
    svg.append(f'    <text x="{x4+card_w//2}" y="{card_y+108}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="{WHITE}">Full mock rounds</text>')
    # Topic panel: Two problems in 60 minutes, once recorded
    svg.append(f'    <rect x="{x4+15}" y="{card_y+150}" width="315" height="195" rx="12" fill="{LIGHT_GREEN}" />')
    svg.append(f'    <text x="{x4+card_w//2}" y="{card_y+210}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{TEXT}">')
    svg.append(f'      <tspan x="{x4+card_w//2}" dy="0">Two problems in </tspan>')
    svg.append(f'      <tspan x="{x4+card_w//2}" dy="36">60 minutes, </tspan>')
    svg.append(f'      <tspan x="{x4+card_w//2}" dy="36">once recorded</tspan>')
    svg.append(f'    </text>')
    # Time panel: Time: 3 mocks of 90 minutes
    svg.append(f'    <rect x="{x4+15}" y="{card_y+365}" width="315" height="105" rx="12" fill="{BG}" stroke="{MAIN_GREEN}" stroke-width="2" />')
    svg.append(f'    <text x="{x4+card_w//2}" y="{card_y+412}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{MAIN_GREEN}">')
    svg.append(f'      <tspan x="{x4+card_w//2}" dy="0">Time: 3 mocks </tspan>')
    svg.append(f'      <tspan x="{x4+card_w//2}" dy="34">of 90 minutes</tspan>')
    svg.append(f'    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Horizontal timeline connections between cards
    svg.append('  <!-- Timeline connecting arrows between week blocks -->')
    svg.append(f'  <line x1="{x1+card_w}" y1="{card_y+65}" x2="{x2}" y2="{card_y+65}" stroke="{MAIN_GREEN}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <line x1="{x2+card_w}" y1="{card_y+65}" x2="{x3}" y2="{card_y+65}" stroke="{MAIN_GREEN}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <line x1="{x3+card_w}" y1="{card_y+65}" x2="{x4}" y2="{card_y+65}" stroke="{MAIN_GREEN}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append('')
    
    # Milestone track for End-of-week test
    # y = 655 to 735 (height = 80)
    # 4 check markers after each week
    track_y = 655
    track_h = 80
    svg.append('  <!-- ==================== END-OF-WEEK TEST MILESTONE TRACK ==================== -->')
    svg.append('  <g id="end-of-week-test-track">')
    svg.append(f'    <rect x="40" y="{track_y}" width="1520" height="{track_h}" rx="14" fill="{LIGHT_GREEN}" stroke="{MAIN_GREEN}" stroke-width="2.5" />')
    
    # 4 check markers aligned with each card center
    centers = [x + card_w//2 for x in xs]
    # Check marker 1
    svg.append(f'    <!-- Check marker after Week 1 -->')
    svg.append(f'    <circle cx="{centers[0]}" cy="{track_y+track_h//2}" r="22" fill="{MAIN_GREEN}" />')
    svg.append(f'    <path d="M {centers[0]-10} {track_y+track_h//2} L {centers[0]-3} {track_y+track_h//2+7} L {centers[0]+10} {track_y+track_h//2-6}" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />')
    
    # Check marker 2
    svg.append(f'    <!-- Check marker after Week 2 -->')
    svg.append(f'    <circle cx="{centers[1]}" cy="{track_y+track_h//2}" r="22" fill="{MAIN_GREEN}" />')
    svg.append(f'    <path d="M {centers[1]-10} {track_y+track_h//2} L {centers[1]-3} {track_y+track_h//2+7} L {centers[1]+10} {track_y+track_h//2-6}" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />')
    
    # Central milestone badge labelled: End-of-week test
    svg.append(f'    <!-- Track Label badge: End-of-week test -->')
    svg.append(f'    <rect x="660" y="{track_y+15}" width="280" height="50" rx="10" fill="{MAIN_GREEN}" />')
    svg.append(f'    <text x="800" y="{track_y+49}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="{WHITE}">End-of-week test</text>')
    
    # Check marker 3
    svg.append(f'    <!-- Check marker after Week 3 -->')
    svg.append(f'    <circle cx="{centers[2]}" cy="{track_y+track_h//2}" r="22" fill="{MAIN_GREEN}" />')
    svg.append(f'    <path d="M {centers[2]-10} {track_y+track_h//2} L {centers[2]-3} {track_y+track_h//2+7} L {centers[2]+10} {track_y+track_h//2-6}" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />')
    
    # Check marker 4
    svg.append(f'    <!-- Check marker after Week 4 -->')
    svg.append(f'    <circle cx="{centers[3]}" cy="{track_y+track_h//2}" r="22" fill="{MAIN_GREEN}" />')
    svg.append(f'    <path d="M {centers[3]-10} {track_y+track_h//2} L {centers[3]-3} {track_y+track_h//2+7} L {centers[3]+10} {track_y+track_h//2-6}" fill="none" stroke="{WHITE}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" />')
    
    # Downward connectors from each card to its check marker
    for c in centers:
        svg.append(f'    <line x1="{c}" y1="{card_y+card_h}" x2="{c}" y2="{track_y}" stroke="{MAIN_GREEN}" stroke-width="3" marker-end="url(#arrow-green)" />')
    svg.append('  </g>')
    svg.append('')
    
    # Bug log bar
    # y = 775 to 865 (height = 90)
    log_y = 775
    log_h = 90
    svg.append('  <!-- ==================== BUG LOG BAR ==================== -->')
    svg.append('  <g id="bug-log-bar">')
    svg.append(f'    <rect x="40" y="{log_y}" width="1520" height="{log_h}" rx="14" fill="{LIGHT_GREEN}" stroke="{MAIN_GREEN}" stroke-width="2.5" />')
    # Icon for log/journal with bug check (56x56)
    svg.append(f'    <g transform="translate(70, {log_y+17})">')
    svg.append(f'      <rect x="6" y="6" width="44" height="44" rx="6" fill="none" stroke="{MAIN_GREEN}" stroke-width="3.5" />')
    svg.append(f'      <line x1="14" y1="18" x2="42" y2="18" stroke="{MAIN_GREEN}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'      <line x1="14" y1="28" x2="42" y2="28" stroke="{MAIN_GREEN}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'      <line x1="14" y1="38" x2="34" y2="38" stroke="{MAIN_GREEN}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'    </g>')
    # Label: Keep a bug log: harness-found bugs are what to practise on
    svg.append(f'    <text x="150" y="{log_y+55}" font-family="sans-serif" font-size="28" font-weight="bold" fill="{TEXT}">Keep a bug log: harness-found bugs are what to practise on</text>')
    svg.append('  </g>')
    svg.append('')
    
    # Takeaway bar / Bottom note
    # y = 905 to 975 (height = 70)
    takeaway_y = 905
    takeaway_h = 70
    svg.append('  <!-- ==================== TAKEAWAY BAR / BOTTOM NOTE ==================== -->')
    svg.append('  <g id="takeaway-bar">')
    svg.append(f'    <rect x="40" y="{takeaway_y}" width="1520" height="{takeaway_h}" rx="12" fill="{MAIN_GREEN}" />')
    svg.append(f'    <text x="800" y="{takeaway_y+44}" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="{WHITE}">Practise the process under time pressure.</text>')
    svg.append('  </g>')
    svg.append('')
    svg.append('</svg>')
    
    return "\n".join(svg)

with open("test_routine.svg", "w") as f:
    f.write(generate_svg())

print("Saved test_routine.svg")
