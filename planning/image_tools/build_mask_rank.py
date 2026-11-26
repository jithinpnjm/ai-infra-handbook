import re
import xml.etree.ElementTree as ET

def generate_svg():
    W = 1600
    H = 1080
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>Worked example: masking numbers to rank distinct errors</title>')
    svg.append('  <desc>Visual pipeline illustrating how masking numbers with sed enables sort and uniq to aggregate distinct error messages across cluster nodes.</desc>')
    
    # Defs
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')
    
    # Main Title (48px bold)
    svg.append('  <text x="800" y="66" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Worked example: masking numbers to rank distinct errors</text>')
    
    # Connecting Arrows between 5 Stage Boxes
    # Box positions:
    # 1: x = 40..312 (w=272)
    # 2: x = 352..624 (w=272)
    # 3: x = 664..936 (w=272)
    # 4: x = 976..1248 (w=272)
    # 5: x = 1288..1560 (w=272)
    # Gaps are exactly 40px: [312, 352], [624, 664], [936, 976], [1248, 1288]
    # Arrows across the 40px gaps at y = 200
    arrow_y = 200
    svg.append(f'  <line x1="312" y1="{arrow_y}" x2="352" y2="{arrow_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <line x1="624" y1="{arrow_y}" x2="664" y2="{arrow_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <line x1="936" y1="{arrow_y}" x2="976" y2="{arrow_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <line x1="1248" y1="{arrow_y}" x2="1288" y2="{arrow_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    
    box_y = 110
    box_h = 820
    box_w = 272
    
    # ==================== STAGE 1: grep -i error train.log ====================
    b1_x = 40
    svg.append('  <!-- ==================== STAGE 1 ==================== -->')
    svg.append(f'  <g id="stage-1">')
    svg.append(f'    <rect x="{b1_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Header: Number circle 1 at (x=68, y=142)
    svg.append(f'    <circle cx="{b1_x + 36}" cy="144" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b1_x + 36}" cy="144" y="153" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">1</text>')
    
    # Outline Icon: Search / Filter (56x56) at (x=b1_x + 180, y=118)
    svg.append(f'    <g transform="translate({b1_x + 180}, 116)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="22" cy="22" r="14" />')
    svg.append('      <line x1="32" y1="32" x2="48" y2="48" stroke-width="5" />')
    svg.append('      <line x1="14" y1="22" x2="30" y2="22" />')
    svg.append('    </g>')
    
    # Command Title: grep -i error train.log (30px bold monospace)
    svg.append(f'    <text x="{b1_x + box_w//2}" y="206" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{b1_x + box_w//2}" dy="0">grep -i error</tspan>')
    svg.append(f'      <tspan x="{b1_x + box_w//2}" dy="36">train.log</tspan>')
    svg.append('    </text>')
    
    # Data table container: y=265, h=645, w=248, x=b1_x+12
    t1_x = b1_x + 12
    t1_w = 248
    svg.append(f'    <rect x="{t1_x}" y="265" width="{t1_w}" height="645" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Line 1: '10:20:01 ERROR NCCL timeout on rank 3' (y=280..415)
    svg.append(f'    <rect x="{t1_x + 8}" y="280" width="{t1_w - 16}" height="135" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t1_x + 20}" y="320" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="0">10:20:01 ERROR</tspan>')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="32">on rank 3</tspan>')
    svg.append('    </text>')
    
    # Line 2: '10:31:09 ERROR NCCL timeout on rank 5' (y=430..565)
    svg.append(f'    <rect x="{t1_x + 8}" y="430" width="{t1_w - 16}" height="135" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t1_x + 20}" y="470" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="0">10:31:09 ERROR</tspan>')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="32">on rank 5</tspan>')
    svg.append('    </text>')
    
    # Line 3: '10:40:00 ERROR CUDA out of memory on gpu=2' (y=580..735)
    svg.append(f'    <rect x="{t1_x + 8}" y="580" width="{t1_w - 16}" height="165" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t1_x + 20}" y="618" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="0">10:40:00 ERROR</tspan>')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="32">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="32">memory on</tspan>')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="32">gpu=2</tspan>')
    svg.append('    </text>')
    
    # Crossed-out line: WARN loss spike (y=760..890)
    svg.append(f'    <rect x="{t1_x + 8}" y="760" width="{t1_w - 16}" height="135" rx="8" fill="#f0f3f1" stroke="#a0aec0" stroke-width="1.5" stroke-dasharray="4,4" />')
    svg.append(f'    <text x="{t1_x + 20}" y="818" font-family="monospace" font-size="24" fill="#718096">')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="0">WARN loss</tspan>')
    svg.append(f'      <tspan x="{t1_x + 20}" dy="32">spike</tspan>')
    svg.append('    </text>')
    # Red cross-out line
    svg.append(f'    <line x1="{t1_x + 16}" y1="840" x2="{t1_x + t1_w - 16}" y2="810" stroke="#c53030" stroke-width="3" />')
    svg.append(f'    <line x1="{t1_x + 16}" y1="810" x2="{t1_x + t1_w - 16}" y2="840" stroke="#c53030" stroke-width="3" />')
    svg.append('  </g>')
    
    # ==================== STAGE 2: sed -E s/[0-9]+/N/g ====================
    b2_x = 352
    svg.append('  <!-- ==================== STAGE 2 ==================== -->')
    svg.append(f'  <g id="stage-2">')
    svg.append(f'    <rect x="{b2_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Header: Number circle 2
    svg.append(f'    <circle cx="{b2_x + 36}" cy="144" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b2_x + 36}" y="153" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">2</text>')
    
    # Outline Icon: Sed / Regex mask (56x56) at (x=b2_x + 180, y=116)
    svg.append(f'    <g transform="translate({b2_x + 180}, 116)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="40" rx="6" />')
    svg.append('      <path d="M 16 28 h 10 M 21 18 v 20" />')
    svg.append('      <path d="M 32 34 l 8 -12" />')
    svg.append('    </g>')
    
    # Command Title: sed -E s/[0-9]+/N/g (30px bold monospace)
    svg.append(f'    <text x="{b2_x + box_w//2}" y="206" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{b2_x + box_w//2}" dy="0">sed -E</tspan>')
    svg.append(f'      <tspan x="{b2_x + box_w//2}" dy="36">s/[0-9]+/N/g</tspan>')
    svg.append('    </text>')
    
    # Data table container: y=265, h=645, w=248, x=b2_x+12
    t2_x = b2_x + 12
    t2_w = 248
    svg.append(f'    <rect x="{t2_x}" y="265" width="{t2_w}" height="645" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Line 1: 'N:N:N ERROR NCCL timeout on rank N' (y=280..445)
    svg.append(f'    <rect x="{t2_x + 8}" y="280" width="{t2_w - 16}" height="145" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t2_x + 20}" y="325" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Line 2 (repeated identical masked NCCL line): 'N:N:N ERROR NCCL timeout on rank N' (y=440..605)
    svg.append(f'    <rect x="{t2_x + 8}" y="440" width="{t2_w - 16}" height="145" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t2_x + 20}" y="485" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Line 3: 'N:N:N ERROR CUDA out of memory on gpu=N' (y=600..780)
    svg.append(f'    <rect x="{t2_x + 8}" y="600" width="{t2_w - 16}" height="175" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t2_x + 20}" y="642" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="32">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="32">memory on</tspan>')
    svg.append(f'      <tspan x="{t2_x + 20}" dy="32">gpu=N</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== STAGE 3: sort ====================
    b3_x = 664
    svg.append('  <!-- ==================== STAGE 3 ==================== -->')
    svg.append(f'  <g id="stage-3">')
    svg.append(f'    <rect x="{b3_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Header: Number circle 3
    svg.append(f'    <circle cx="{b3_x + 36}" cy="144" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b3_x + 36}" y="153" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">3</text>')
    
    # Outline Icon: Sort bars (56x56) at (x=b3_x + 180, y=116)
    svg.append(f'    <g transform="translate({b3_x + 180}, 116)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="8" y1="12" x2="48" y2="12" stroke-width="4" />')
    svg.append('      <line x1="8" y1="24" x2="38" y2="24" stroke-width="4" />')
    svg.append('      <line x1="8" y1="36" x2="28" y2="36" stroke-width="4" />')
    svg.append('      <line x1="8" y1="48" x2="18" y2="48" stroke-width="4" />')
    svg.append('    </g>')
    
    # Command Title: sort (30px bold monospace)
    svg.append(f'    <text x="{b3_x + box_w//2}" y="224" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">sort</text>')
    
    # Data table container: y=265, h=645, w=248, x=b3_x+12
    t3_x = b3_x + 12
    t3_w = 248
    svg.append(f'    <rect x="{t3_x}" y="265" width="{t3_w}" height="645" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Visual grouping bracket container for the two identical NCCL lines
    svg.append(f'    <rect x="{t3_x + 6}" y="276" width="{t3_w - 12}" height="300" rx="8" fill="#d2e5d7" stroke="#207448" stroke-width="2" />')
    
    # Row 1 inside bracket
    svg.append(f'    <rect x="{t3_x + 12}" y="284" width="{t3_w - 24}" height="135" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t3_x + 22}" y="324" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t3_x + 22}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t3_x + 22}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t3_x + 22}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Row 2 inside bracket
    svg.append(f'    <rect x="{t3_x + 12}" y="430" width="{t3_w - 24}" height="135" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t3_x + 22}" y="470" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t3_x + 22}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t3_x + 22}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t3_x + 22}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Grouping label
    svg.append(f'    <text x="{t3_x + t3_w//2}" y="610" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{t3_x + t3_w//2}" dy="0">groups the two</tspan>')
    svg.append(f'      <tspan x="{t3_x + t3_w//2}" dy="30">identical NCCL</tspan>')
    svg.append(f'      <tspan x="{t3_x + t3_w//2}" dy="30">lines next to</tspan>')
    svg.append(f'      <tspan x="{t3_x + t3_w//2}" dy="30">each other</tspan>')
    svg.append('    </text>')
    
    # Row 3: CUDA error
    svg.append(f'    <rect x="{t3_x + 8}" y="735" width="{t3_w - 16}" height="160" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t3_x + 20}" y="772" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t3_x + 20}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t3_x + 20}" dy="32">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t3_x + 20}" dy="32">memory on</tspan>')
    svg.append(f'      <tspan x="{t3_x + 20}" dy="32">gpu=N</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== STAGE 4: uniq -c ====================
    b4_x = 976
    svg.append('  <!-- ==================== STAGE 4 ==================== -->')
    svg.append(f'  <g id="stage-4">')
    svg.append(f'    <rect x="{b4_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Header: Number circle 4
    svg.append(f'    <circle cx="{b4_x + 36}" cy="144" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b4_x + 36}" y="153" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">4</text>')
    
    # Outline Icon: Uniq / Aggregate count (56x56) at (x=b4_x + 180, y=116)
    svg.append(f'    <g transform="translate({b4_x + 180}, 116)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="10" width="38" height="14" rx="3" />')
    svg.append('      <rect x="8" y="30" width="38" height="14" rx="3" />')
    svg.append('      <line x1="16" y1="17" x2="22" y2="17" stroke-width="3" />')
    svg.append('      <line x1="16" y1="37" x2="22" y2="37" stroke-width="3" />')
    svg.append('    </g>')
    
    # Command Title: uniq -c (30px bold monospace)
    svg.append(f'    <text x="{b4_x + box_w//2}" y="224" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">uniq -c</text>')
    
    # Data table container: y=265, h=645, w=248, x=b4_x+12
    t4_x = b4_x + 12
    t4_w = 248
    svg.append(f'    <rect x="{t4_x}" y="265" width="{t4_w}" height="645" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Line 1: '2 N:N:N ERROR NCCL timeout on rank N' (y=340..500)
    svg.append(f'    <rect x="{t4_x + 8}" y="340" width="{t4_w - 16}" height="155" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append(f'    <text x="{t4_x + 20}" y="385" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t4_x + 20}" dy="0" font-weight="bold" fill="#207448">2 </tspan><tspan>N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t4_x + 20}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t4_x + 20}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Line 2: '1 N:N:N ERROR CUDA out of memory on gpu=N' (y=540..730)
    svg.append(f'    <rect x="{t4_x + 8}" y="540" width="{t4_w - 16}" height="185" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append(f'    <text x="{t4_x + 20}" y="582" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t4_x + 20}" dy="0" font-weight="bold" fill="#207448">1 </tspan><tspan>N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t4_x + 20}" dy="32">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t4_x + 20}" dy="32">memory on</tspan>')
    svg.append(f'      <tspan x="{t4_x + 20}" dy="32">gpu=N</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== STAGE 5: sort -rn | head ====================
    b5_x = 1288
    svg.append('  <!-- ==================== STAGE 5 ==================== -->')
    svg.append(f'  <g id="stage-5">')
    svg.append(f'    <rect x="{b5_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Header: Number circle 5
    svg.append(f'    <circle cx="{b5_x + 36}" cy="144" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b5_x + 36}" y="153" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">5</text>')
    
    # Outline Icon: Top-ranked podium / filter (56x56) at (x=b5_x + 180, y=116)
    svg.append(f'    <g transform="translate({b5_x + 180}, 116)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="12,10 44,10 32,28 32,46 24,46 24,28" />')
    svg.append('      <line x1="16" y1="18" x2="40" y2="18" stroke-width="3" />')
    svg.append('    </g>')
    
    # Command Title: sort -rn | head (30px bold monospace)
    svg.append(f'    <text x="{b5_x + box_w//2}" y="206" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{b5_x + box_w//2}" dy="0">sort -rn |</tspan>')
    svg.append(f'      <tspan x="{b5_x + box_w//2}" dy="36">head</tspan>')
    svg.append('    </text>')
    
    # Data table container: y=265, h=645, w=248, x=b5_x+12
    t5_x = b5_x + 12
    t5_w = 248
    svg.append(f'    <rect x="{t5_x}" y="265" width="{t5_w}" height="645" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Annotation note: ranks them with the count 2 line first
    svg.append(f'    <text x="{t5_x + t5_w//2}" y="310" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append(f'      <tspan x="{t5_x + t5_w//2}" dy="0">ranks them</tspan>')
    svg.append(f'      <tspan x="{t5_x + t5_w//2}" dy="30">with the count</tspan>')
    svg.append(f'      <tspan x="{t5_x + t5_w//2}" dy="30">2 line first</tspan>')
    svg.append('    </text>')
    
    # Single Orange Highlight: Count 2 line first!
    # stroke="#db8129", fill="#fff5ea" (EXACTLY ONE ORANGE ELEMENT in the SVG)
    svg.append(f'    <rect x="{t5_x + 8}" y="420" width="{t5_w - 16}" height="160" rx="8" fill="#fff5ea" stroke="#db8129" stroke-width="3.5" />')
    svg.append(f'    <text x="{t5_x + 20}" y="465" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t5_x + 20}" dy="0" font-weight="bold">2 </tspan><tspan>N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t5_x + 20}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t5_x + 20}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Line 2: '1 N:N:N ERROR CUDA out of memory on gpu=N' (y=620..810)
    svg.append(f'    <rect x="{t5_x + 8}" y="620" width="{t5_w - 16}" height="185" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append(f'    <text x="{t5_x + 20}" y="662" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t5_x + 20}" dy="0" font-weight="bold">1 </tspan><tspan>N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t5_x + 20}" dy="32">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t5_x + 20}" dy="32">memory on</tspan>')
    svg.append(f'      <tspan x="{t5_x + 20}" dy="32">gpu=N</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== BOTTOM NOTE / TAKEAWAY BAR ====================
    # y = 970 to 1040 (h = 70, gap = 40, margin bottom = 40)
    svg.append('  <!-- ==================== TAKEAWAY BAR ==================== -->')
    svg.append('  <g id="takeaway-bar">')
    svg.append('    <rect x="40" y="970" width="1520" height="70" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <text x="800" y="1014" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Masking the numbers makes different ranks the same message, so uniq can count them</text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == '__main__':
    with open('test_pipeline.svg', 'w') as f:
        f.write(generate_svg())
    print("Generated test_pipeline.svg successfully!")
