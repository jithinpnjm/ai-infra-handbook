import re
import xml.etree.ElementTree as ET

def generate_svg():
    W = 1600
    H = 1120
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>Worked example: masking numbers to rank distinct errors</title>')
    svg.append('  <desc>Five-stage pipeline demonstrating how masking numbers with sed allows sorting and uniq to aggregate distinct error messages across cluster nodes.</desc>')
    
    # Defs
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')
    
    # Main Title (48px bold)
    svg.append('  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Worked example: masking numbers to rank distinct errors</text>')
    
    # Box layout parameters
    # 5 boxes of width 272 across [40..1560]
    # Gaps of 40px: [312, 352], [624, 664], [936, 976], [1248, 1288]
    box_y = 110
    box_h = 860
    box_w = 272
    
    # 4 Connecting Arrows across the 40px gaps
    arrow_y = 145
    svg.append(f'  <line x1="312" y1="{arrow_y}" x2="352" y2="{arrow_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <line x1="624" y1="{arrow_y}" x2="664" y2="{arrow_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <line x1="936" y1="{arrow_y}" x2="976" y2="{arrow_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <line x1="1248" y1="{arrow_y}" x2="1288" y2="{arrow_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    
    # Inner card width & margins
    card_w = 244
    card_margin_x = 14
    
    # ==================== STAGE 1 ====================
    b1_x = 40
    svg.append('  <!-- ==================== STAGE 1: grep -i error train.log ==================== -->')
    svg.append('  <g id="stage-1">')
    svg.append(f'    <rect x="{b1_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Number circle 1
    svg.append(f'    <circle cx="{b1_x + 40}" cy="145" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b1_x + 40}" y="154" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">1</text>')
    
    # Outline Icon: Filter / Search (56px)
    svg.append(f'    <g transform="translate({b1_x + 180}, 117)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="22" cy="22" r="14" />')
    svg.append('      <line x1="32" y1="32" x2="48" y2="48" stroke-width="5" />')
    svg.append('      <line x1="14" y1="22" x2="30" y2="22" />')
    svg.append('    </g>')
    
    # Title: grep -i error train.log (30px bold monospace)
    svg.append(f'    <text x="{b1_x + box_w//2}" y="206" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{b1_x + box_w//2}" dy="0">grep -i</tspan>')
    svg.append(f'      <tspan x="{b1_x + box_w//2}" dy="34">error</tspan>')
    svg.append(f'      <tspan x="{b1_x + box_w//2}" dy="34">train.log</tspan>')
    svg.append('    </text>')
    
    # Inner Data Table Container
    t1_x = b1_x + card_margin_x
    t1_y = 295
    t1_h = 655
    svg.append(f'    <rect x="{t1_x}" y="{t1_y}" width="{card_w}" height="{t1_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Row 1: 10:20:01 ERROR NCCL timeout on rank 3
    svg.append(f'    <rect x="{t1_x + 8}" y="{t1_y + 12}" width="{card_w - 16}" height="144" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t1_x + 26}" y="{t1_y + 48}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="0">10:20:01</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">ERROR NCCL</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">timeout on</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">rank 3</tspan>')
    svg.append('    </text>')
    
    # Row 2: 10:31:09 ERROR NCCL timeout on rank 5
    svg.append(f'    <rect x="{t1_x + 8}" y="{t1_y + 168}" width="{card_w - 16}" height="144" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t1_x + 26}" y="{t1_y + 204}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="0">10:31:09</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">ERROR NCCL</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">timeout on</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">rank 5</tspan>')
    svg.append('    </text>')
    
    # Row 3: 10:40:00 ERROR CUDA out of memory on gpu=2
    svg.append(f'    <rect x="{t1_x + 8}" y="{t1_y + 324}" width="{card_w - 16}" height="172" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t1_x + 26}" y="{t1_y + 360}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="0">10:40:00</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">ERROR CUDA</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">out of memory</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="28">on gpu=2</tspan>')
    svg.append('    </text>')
    
    # Row 4 (Crossed out): WARN loss spike
    svg.append(f'    <rect x="{t1_x + 8}" y="{t1_y + 508}" width="{card_w - 16}" height="135" rx="8" fill="#f0f3f1" stroke="#a0aec0" stroke-width="1.5" stroke-dasharray="4,4" />')
    svg.append(f'    <text x="{t1_x + 26}" y="{t1_y + 565}" font-family="monospace" font-size="24" fill="#718096">')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="0">WARN loss</tspan>')
    svg.append(f'      <tspan x="{t1_x + 26}" dy="32">spike</tspan>')
    svg.append('    </text>')
    # Red strike-through
    svg.append(f'    <line x1="{t1_x + 16}" y1="{t1_y + 588}" x2="{t1_x + card_w - 16}" y2="{t1_y + 560}" stroke="#c53030" stroke-width="3" />')
    svg.append(f'    <line x1="{t1_x + 16}" y1="{t1_y + 560}" x2="{t1_x + card_w - 16}" y2="{t1_y + 588}" stroke="#c53030" stroke-width="3" />')
    svg.append('  </g>')
    
    # ==================== STAGE 2 ====================
    b2_x = 352
    svg.append('  <!-- ==================== STAGE 2: sed -E s/[0-9]+/N/g ==================== -->')
    svg.append('  <g id="stage-2">')
    svg.append(f'    <rect x="{b2_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Number circle 2
    svg.append(f'    <circle cx="{b2_x + 40}" cy="145" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b2_x + 40}" y="154" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">2</text>')
    
    # Outline Icon: Sed / regex replace (56px)
    svg.append(f'    <g transform="translate({b2_x + 180}, 117)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="40" rx="6" />')
    svg.append('      <path d="M 16 28 h 10 M 21 18 v 20" />')
    svg.append('      <path d="M 32 34 l 8 -12" />')
    svg.append('    </g>')
    
    # Title: sed -E s/[0-9]+/N/g (30px bold monospace)
    svg.append(f'    <text x="{b2_x + box_w//2}" y="222" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{b2_x + box_w//2}" dy="0">sed -E</tspan>')
    svg.append(f'      <tspan x="{b2_x + box_w//2}" dy="36">s/[0-9]+/N/g</tspan>')
    svg.append('    </text>')
    
    # Inner Data Table Container
    t2_x = b2_x + card_margin_x
    t2_y = 295
    t2_h = 655
    svg.append(f'    <rect x="{t2_x}" y="{t2_y}" width="{card_w}" height="{t2_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Row 1: N:N:N ERROR NCCL timeout on rank N
    svg.append(f'    <rect x="{t2_x + 8}" y="{t2_y + 12}" width="{card_w - 16}" height="145" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t2_x + 26}" y="{t2_y + 54}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Row 2 (Second copy): N:N:N ERROR NCCL timeout on rank N
    svg.append(f'    <rect x="{t2_x + 8}" y="{t2_y + 172}" width="{card_w - 16}" height="145" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t2_x + 26}" y="{t2_y + 214}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Row 3: N:N:N ERROR CUDA out of memory on gpu=N
    svg.append(f'    <rect x="{t2_x + 8}" y="{t2_y + 332}" width="{card_w - 16}" height="175" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t2_x + 26}" y="{t2_y + 374}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="32">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="32">memory on</tspan>')
    svg.append(f'      <tspan x="{t2_x + 26}" dy="32">gpu=N</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== STAGE 3 ====================
    b3_x = 664
    svg.append('  <!-- ==================== STAGE 3: sort ==================== -->')
    svg.append('  <g id="stage-3">')
    svg.append(f'    <rect x="{b3_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Number circle 3
    svg.append(f'    <circle cx="{b3_x + 40}" cy="145" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b3_x + 40}" y="154" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">3</text>')
    
    # Outline Icon: Sort bars (56px)
    svg.append(f'    <g transform="translate({b3_x + 180}, 117)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="8" y1="12" x2="48" y2="12" stroke-width="4" />')
    svg.append('      <line x1="8" y1="24" x2="38" y2="24" stroke-width="4" />')
    svg.append('      <line x1="8" y1="36" x2="28" y2="36" stroke-width="4" />')
    svg.append('      <line x1="8" y1="48" x2="18" y2="48" stroke-width="4" />')
    svg.append('    </g>')
    
    # Title: sort (30px bold monospace)
    svg.append(f'    <text x="{b3_x + box_w//2}" y="240" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">sort</text>')
    
    # Inner Data Table Container
    t3_x = b3_x + card_margin_x
    t3_y = 295
    t3_h = 655
    svg.append(f'    <rect x="{t3_x}" y="{t3_y}" width="{card_w}" height="{t3_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Grouping bracket container around the two NCCL lines
    svg.append(f'    <rect x="{t3_x + 6}" y="{t3_y + 10}" width="{card_w - 12}" height="305" rx="8" fill="#d2e5d7" stroke="#207448" stroke-width="2" />')
    
    # Grouped line 1
    svg.append(f'    <rect x="{t3_x + 12}" y="{t3_y + 18}" width="{card_w - 24}" height="135" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t3_x + 28}" y="{t3_y + 54}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t3_x + 28}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t3_x + 28}" dy="30">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t3_x + 28}" dy="30">on rank N</tspan>')
    svg.append('    </text>')
    
    # Grouped line 2
    svg.append(f'    <rect x="{t3_x + 12}" y="{t3_y + 165}" width="{card_w - 24}" height="135" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t3_x + 28}" y="{t3_y + 201}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t3_x + 28}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t3_x + 28}" dy="30">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t3_x + 28}" dy="30">on rank N</tspan>')
    svg.append('    </text>')
    
    # Grouping Annotation Label: groups the two identical NCCL lines next to each other
    svg.append(f'    <text x="{t3_x + card_w//2}" y="{t3_y + 355}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{t3_x + card_w//2}" dy="0">groups the two</tspan>')
    svg.append(f'      <tspan x="{t3_x + card_w//2}" dy="30">identical NCCL</tspan>')
    svg.append(f'      <tspan x="{t3_x + card_w//2}" dy="30">lines next to</tspan>')
    svg.append(f'      <tspan x="{t3_x + card_w//2}" dy="30">each other</tspan>')
    svg.append('    </text>')
    
    # Line 3: N:N:N ERROR CUDA out of memory on gpu=N
    svg.append(f'    <rect x="{t3_x + 8}" y="{t3_y + 490}" width="{card_w - 16}" height="155" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'    <text x="{t3_x + 26}" y="{t3_y + 526}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t3_x + 26}" dy="0">N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t3_x + 26}" dy="30">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t3_x + 26}" dy="30">memory on</tspan>')
    svg.append(f'      <tspan x="{t3_x + 26}" dy="30">gpu=N</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== STAGE 4 ====================
    b4_x = 976
    svg.append('  <!-- ==================== STAGE 4: uniq -c ==================== -->')
    svg.append('  <g id="stage-4">')
    svg.append(f'    <rect x="{b4_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Number circle 4
    svg.append(f'    <circle cx="{b4_x + 40}" cy="145" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b4_x + 40}" y="154" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">4</text>')
    
    # Outline Icon: Uniq count (56px)
    svg.append(f'    <g transform="translate({b4_x + 180}, 117)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="10" width="38" height="14" rx="3" />')
    svg.append('      <rect x="8" y="30" width="38" height="14" rx="3" />')
    svg.append('      <line x1="16" y1="17" x2="22" y2="17" stroke-width="3" />')
    svg.append('      <line x1="16" y1="37" x2="22" y2="37" stroke-width="3" />')
    svg.append('    </g>')
    
    # Title: uniq -c (30px bold monospace)
    svg.append(f'    <text x="{b4_x + box_w//2}" y="240" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">uniq -c</text>')
    
    # Inner Data Table Container
    t4_x = b4_x + card_margin_x
    t4_y = 295
    t4_h = 655
    svg.append(f'    <rect x="{t4_x}" y="{t4_y}" width="{card_w}" height="{t4_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Line 1: 2 N:N:N ERROR NCCL timeout on rank N
    svg.append(f'    <rect x="{t4_x + 8}" y="{t4_y + 110}" width="{card_w - 16}" height="160" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append(f'    <text x="{t4_x + 26}" y="{t4_y + 155}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t4_x + 26}" dy="0" font-weight="bold" fill="#207448">2 </tspan><tspan>N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t4_x + 26}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t4_x + 26}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Line 2: 1 N:N:N ERROR CUDA out of memory on gpu=N
    svg.append(f'    <rect x="{t4_x + 8}" y="{t4_y + 350}" width="{card_w - 16}" height="185" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append(f'    <text x="{t4_x + 26}" y="{t4_y + 395}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t4_x + 26}" dy="0" font-weight="bold" fill="#207448">1 </tspan><tspan>N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t4_x + 26}" dy="32">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t4_x + 26}" dy="32">memory on</tspan>')
    svg.append(f'      <tspan x="{t4_x + 26}" dy="32">gpu=N</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== STAGE 5 ====================
    b5_x = 1288
    svg.append('  <!-- ==================== STAGE 5: sort -rn | head ==================== -->')
    svg.append('  <g id="stage-5">')
    svg.append(f'    <rect x="{b5_x}" y="{box_y}" width="{box_w}" height="{box_h}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    
    # Number circle 5
    svg.append(f'    <circle cx="{b5_x + 40}" cy="145" r="24" fill="#207448" />')
    svg.append(f'    <text x="{b5_x + 40}" y="154" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">5</text>')
    
    # Outline Icon: Top-ranked podium (56px)
    svg.append(f'    <g transform="translate({b5_x + 180}, 117)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="12,10 44,10 32,28 32,46 24,46 24,28" />')
    svg.append('      <line x1="16" y1="18" x2="40" y2="18" stroke-width="3" />')
    svg.append('    </g>')
    
    # Title: sort -rn | head (30px bold monospace)
    svg.append(f'    <text x="{b5_x + box_w//2}" y="222" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">')
    svg.append(f'      <tspan x="{b5_x + box_w//2}" dy="0">sort -rn |</tspan>')
    svg.append(f'      <tspan x="{b5_x + box_w//2}" dy="36">head</tspan>')
    svg.append('    </text>')
    
    # Inner Data Table Container
    t5_x = b5_x + card_margin_x
    t5_y = 295
    t5_h = 655
    svg.append(f'    <rect x="{t5_x}" y="{t5_y}" width="{card_w}" height="{t5_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Annotation Label: ranks them with the count 2 line first
    svg.append(f'    <text x="{t5_x + card_w//2}" y="{t5_y + 45}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append(f'      <tspan x="{t5_x + card_w//2}" dy="0">ranks them</tspan>')
    svg.append(f'      <tspan x="{t5_x + card_w//2}" dy="30">with the count</tspan>')
    svg.append(f'      <tspan x="{t5_x + card_w//2}" dy="30">2 line first</tspan>')
    svg.append('    </text>')
    
    # Single Orange Highlight: Count 2 line first!
    # Exactly one orange element: #db8129 stroke and fill="#fff5ea"
    svg.append(f'    <rect x="{t5_x + 8}" y="{t5_y + 160}" width="{card_w - 16}" height="165" rx="8" fill="#fff5ea" stroke="#db8129" stroke-width="3.5" />')
    svg.append(f'    <text x="{t5_x + 26}" y="{t5_y + 205}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t5_x + 26}" dy="0" font-weight="bold">2 </tspan><tspan>N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t5_x + 26}" dy="32">NCCL timeout</tspan>')
    svg.append(f'      <tspan x="{t5_x + 26}" dy="32">on rank N</tspan>')
    svg.append('    </text>')
    
    # Line 2: 1 N:N:N ERROR CUDA out of memory on gpu=N
    svg.append(f'    <rect x="{t5_x + 8}" y="{t5_y + 390}" width="{card_w - 16}" height="185" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append(f'    <text x="{t5_x + 26}" y="{t5_y + 435}" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append(f'      <tspan x="{t5_x + 26}" dy="0" font-weight="bold">1 </tspan><tspan>N:N:N ERROR</tspan>')
    svg.append(f'      <tspan x="{t5_x + 26}" dy="32">CUDA out of</tspan>')
    svg.append(f'      <tspan x="{t5_x + 26}" dy="32">memory on</tspan>')
    svg.append(f'      <tspan x="{t5_x + 26}" dy="32">gpu=N</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    
    # ==================== BOTTOM TAKEAWAY BAR ====================
    # y = 1010 to 1080 (h=70, top gap = 1010 - 970 = 40, bottom margin = 1120 - 1080 = 40)
    svg.append('  <!-- ==================== TAKEAWAY BAR ==================== -->')
    svg.append('  <g id="takeaway-bar">')
    svg.append('    <rect x="40" y="1010" width="1520" height="70" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <text x="800" y="1054" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Masking the numbers makes different ranks the same message, so uniq can count them</text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == '__main__':
    with open('test_pipeline.svg', 'w') as f:
        f.write(generate_svg())
    print("Regenerated test_pipeline.svg successfully!")
