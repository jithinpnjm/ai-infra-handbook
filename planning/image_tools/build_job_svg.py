import xml.etree.ElementTree as ET
import re

def build_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">')
    svg.append('  <title>Checkpoint before the time limit: SIGUSR1 reaches the batch shell, then the trainer</title>')
    svg.append('  <desc>Slurm job checkpointing architecture showing SIGUSR1 propagation to batch shell and background python trainer</desc>')
    
    # Defs
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 16 16" refX="14" refY="8" markerWidth="14" markerHeight="14" orient="auto-start-reverse">')
    svg.append('      <path d="M 0 2 L 14 8 L 0 14 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 16 16" refX="14" refY="8" markerWidth="14" markerHeight="14" orient="auto-start-reverse">')
    svg.append('      <path d="M 0 2 L 14 8 L 0 14 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Canvas background
    svg.append('  <rect x="0" y="0" width="1600" height="1200" fill="#f5f8f5" />')
    
    # Title
    svg.append('  <!-- Title -->')
    svg.append('  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#207448">Checkpoint before the time limit: <tspan x="800" dy="52" font-size="48" fill="#303a36">SIGUSR1 reaches the batch shell, then the trainer</tspan></text>')
    
    # Timeline Container
    svg.append('  <!-- Timeline Section -->')
    svg.append('  <rect x="60" y="135" width="1480" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    
    # Timeline track line
    svg.append('  <line x1="100" y1="245" x2="1500" y2="245" stroke="#207448" stroke-width="6" stroke-linecap="round" />')
    
    # Timeline Left end: 'Job starts'
    svg.append('  <circle cx="100" cy="245" r="10" fill="#207448" />')
    svg.append('  <rect x="90" y="155" width="180" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('  <text x="180" y="191" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">Job starts</text>')
    
    # Timeline Marker (180 seconds before right end): Key Event (Orange)
    # Marker pin on timeline
    marker_x = 760
    svg.append(f'  <circle cx="{marker_x}" cy="245" r="12" fill="#db8129" />')
    svg.append(f'  <line x1="{marker_x}" y1="225" x2="{marker_x}" y2="245" stroke="#db8129" stroke-width="4" />')
    # Orange card for marker
    card_w = 700
    card_x = marker_x - card_w // 2
    svg.append(f'  <rect x="{card_x}" y="152" width="{card_w}" height="70" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    svg.append(f'  <text x="{marker_x}" y="180" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129">#SBATCH --signal=B:USR1@180: <tspan x="{marker_x}" dy="28" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">Slurm sends SIGUSR1 to the batch shell</tspan></text>')
    
    # Timeline Right end: 'Time limit: SIGTERM, then SIGKILL after KillWait (default 30 s)'
    svg.append('  <circle cx="1500" cy="245" r="10" fill="#207448" />')
    svg.append('  <rect x="1140" y="145" width="380" height="90" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('  <text x="1330" y="172" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="1330" dy="0">Time limit: SIGTERM,</tspan>')
    svg.append('    <tspan x="1330" dy="28">then SIGKILL after</tspan>')
    svg.append('    <tspan x="1330" dy="28">KillWait (default 30 s)</tspan>')
    svg.append('  </text>')
    
    # Arrow 1: From Timeline Marker down to Box 1
    # Circle (1) in orange
    svg.append('  <!-- Arrow 1: Slurm sends SIGUSR1 to the batch shell -->')
    arrow1_x = 450
    # Pin from timeline marker down to Box 1
    svg.append(f'  <path d="M {marker_x} 257 V 290 H {arrow1_x} V 360" fill="none" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />')
    svg.append(f'  <circle cx="{arrow1_x}" cy="305" r="24" fill="#db8129" />')
    svg.append(f'  <text x="{arrow1_x}" y="313" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>')
    svg.append(f'  <text x="{arrow1_x + 40}" y="325" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">Slurm sends SIGUSR1 to the batch shell</text>')
    
    # Process Column (Left)
    col_x = 60
    col_w = 900
    
    # Box 1: Batch shell (script) with 'trap kill -USR1 $pid; wait $pid USR1'
    b1_y = 360
    b1_h = 160
    svg.append('  <!-- Box 1: Batch shell (script) -->')
    svg.append(f'  <rect x="{col_x}" y="{b1_y}" width="{col_w}" height="{b1_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Icon for Box 1 (terminal window)
    svg.append(f'  <g transform="translate({col_x + 30}, {b1_y + 20})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="2" y="4" width="52" height="42" rx="6" />')
    svg.append('    <line x1="2" y1="16" x2="54" y2="16" />')
    svg.append('    <polyline points="10,26 18,34 10,42" />')
    svg.append('    <line x1="24" y1="42" x2="38" y2="42" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{col_x + 105}" y="{b1_y + 55}" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Batch shell (script)</text>')
    # Subpanel for trap code
    svg.append(f'  <rect x="{col_x + 30}" y="{b1_y + 85}" width="{col_w - 60}" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  <text x="{col_x + 50}" y="{b1_y + 120}" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">trap kill -USR1 $pid; wait $pid USR1</text>')
    
    # Arrow 2: Loop on Box 1
    # 'trap fires at once because the shell is in wait, not in a foreground command'
    svg.append('  <!-- Arrow 2: trap fires at once -->')
    loop2_x = col_x + col_w
    svg.append(f'  <path d="M {loop2_x} {b1_y + 50} H {loop2_x + 45} V {b1_y + 115} H {loop2_x}" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append(f'  <circle cx="{loop2_x + 45}" cy="{b1_y + 82}" r="24" fill="#207448" />')
    svg.append(f'  <text x="{loop2_x + 45}" y="{b1_y + 90}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>')
    svg.append(f'  <text x="{loop2_x + 85}" y="{b1_y + 60}" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'    <tspan x="{loop2_x + 85}" dy="0">trap fires at once because</tspan>')
    svg.append(f'    <tspan x="{loop2_x + 85}" dy="30">the shell is in wait, not in</tspan>')
    svg.append(f'    <tspan x="{loop2_x + 85}" dy="30">a foreground command</tspan>')
    svg.append('  </text>')
    
    # Arrow 3: Between Box 1 and Box 2
    b2_y = 580
    b2_h = 160
    arrow3_x = 350
    svg.append('  <!-- Arrow 3: kill -USR1 forwards the signal to the training process -->')
    svg.append(f'  <line x1="{arrow3_x}" y1="{b1_y + b1_h}" x2="{arrow3_x}" y2="{b2_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <circle cx="{arrow3_x}" cy="{(b1_y + b1_h + b2_y)//2}" r="24" fill="#207448" />')
    svg.append(f'  <text x="{arrow3_x}" y="{(b1_y + b1_h + b2_y)//2 + 8}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>')
    svg.append(f'  <text x="{arrow3_x + 40}" y="{(b1_y + b1_h + b2_y)//2 - 4}" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'    <tspan x="{arrow3_x + 40}" dy="0">kill -USR1 forwards the signal</tspan>')
    svg.append(f'    <tspan x="{arrow3_x + 40}" dy="28">to the training process</tspan>')
    svg.append('  </text>')
    
    # Box 2: python train.py running in the background (&), pid saved in $pid
    svg.append('  <!-- Box 2: python train.py running in the background -->')
    svg.append(f'  <rect x="{col_x}" y="{b2_y}" width="{col_w}" height="{b2_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Icon for Box 2 (CPU chip)
    svg.append(f'  <g transform="translate({col_x + 30}, {b2_y + 25})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="10" y="10" width="36" height="36" rx="6" />')
    svg.append('    <circle cx="28" cy="28" r="8" />')
    svg.append('    <line x1="18" y1="2" x2="18" y2="10" /><line x1="28" y1="2" x2="28" y2="10" /><line x1="38" y1="2" x2="38" y2="10" />')
    svg.append('    <line x1="18" y1="46" x2="18" y2="54" /><line x1="28" y1="46" x2="28" y2="54" /><line x1="38" y1="46" x2="38" y2="54" />')
    svg.append('    <line x1="2" y1="18" x2="10" y2="18" /><line x1="2" y1="28" x2="10" y2="28" /><line x1="2" y1="38" x2="10" y2="38" />')
    svg.append('    <line x1="46" y1="18" x2="54" y2="18" /><line x1="46" y1="28" x2="54" y2="28" /><line x1="46" y1="38" x2="54" y2="38" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{col_x + 105}" y="{b2_y + 65}" font-family="monospace" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append(f'    <tspan x="{col_x + 105}" dy="0">python train.py</tspan>')
    svg.append(f'    <tspan x="{col_x + 105}" dy="42" font-family="sans-serif" font-size="24" font-weight="normal">running in the background (&amp;), pid saved in $pid</tspan>')
    svg.append('  </text>')
    
    # Arrow 4: Loop on Box 2
    # 'training writes the checkpoint'
    svg.append('  <!-- Arrow 4: training writes the checkpoint -->')
    loop4_x = col_x + col_w
    svg.append(f'  <path d="M {loop4_x} {b2_y + 50} H {loop4_x + 45} V {b2_y + 115} H {loop4_x}" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append(f'  <circle cx="{loop4_x + 45}" cy="{b2_y + 82}" r="24" fill="#207448" />')
    svg.append(f'  <text x="{loop4_x + 45}" y="{b2_y + 90}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>')
    svg.append(f'  <text x="{loop4_x + 85}" y="{b2_y + 90}" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">training writes the checkpoint</text>')
    
    # Arrow 5: Between Box 2 and Box 3
    b3_y = 800
    b3_h = 130
    arrow5_x = 350
    svg.append('  <!-- Arrow 5: wait returns, job ends cleanly -->')
    svg.append(f'  <line x1="{arrow5_x}" y1="{b2_y + b2_h}" x2="{arrow5_x}" y2="{b3_y}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <circle cx="{arrow5_x}" cy="{(b2_y + b2_h + b3_y)//2}" r="24" fill="#207448" />')
    svg.append(f'  <text x="{arrow5_x}" y="{(b2_y + b2_h + b3_y)//2 + 8}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>')
    svg.append(f'  <text x="{arrow5_x + 40}" y="{(b2_y + b2_h + b3_y)//2 + 8}" font-family="sans-serif" font-size="24" fill="#303a36">wait returns, job ends cleanly</text>')
    
    # Box 3: the batch shell line 'wait $pid'
    svg.append('  <!-- Box 3: wait $pid -->')
    svg.append(f'  <rect x="{col_x}" y="{b3_y}" width="{col_w}" height="{b3_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Icon for Box 3 (clock timer)
    svg.append(f'  <g transform="translate({col_x + 30}, {b3_y + 35})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="28" cy="28" r="22" />')
    svg.append('    <polyline points="28,14 28,28 38,28" />')
    svg.append('    <line x1="24" y1="2" x2="32" y2="2" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{col_x + 105}" y="{b3_y + 75}" font-family="monospace" font-size="32" font-weight="bold" fill="#207448">wait $pid</text>')
    
    # Contrast Box to the right
    contrast_x = 1010
    contrast_y = 750
    contrast_w = 530
    contrast_h = 180
    svg.append('  <!-- Contrast Box -->')
    svg.append(f'  <rect x="{contrast_x}" y="{contrast_y}" width="{contrast_w}" height="{contrast_h}" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" />')
    # Warning icon for Contrast Box
    svg.append(f'  <g transform="translate({contrast_x + 30}, {contrast_y + 25})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 28 6 L 50 48 L 6 48 Z" />')
    svg.append('    <line x1="28" y1="20" x2="28" y2="34" />')
    svg.append('    <circle cx="28" cy="42" r="2" fill="#207448" />')
    svg.append('  </g>')
    svg.append(f'  <text x="{contrast_x + 105}" y="{contrast_y + 45}" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'    <tspan x="{contrast_x + 105}" dy="0">If python train.py ran in the</tspan>')
    svg.append(f'    <tspan x="{contrast_x + 105}" dy="32">foreground, the shell would</tspan>')
    svg.append(f'    <tspan x="{contrast_x + 105}" dy="32">defer the trap until it</tspan>')
    svg.append(f'    <tspan x="{contrast_x + 105}" dy="32">finished</tspan>')
    svg.append('  </text>')
    
    # Bottom bar: 'Start long-running children in the background and wait for them'
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <rect x="60" y="1030" width="1480" height="90" rx="12" fill="#207448" />')
    svg.append('  <text x="800" y="1086" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Start long-running children in the background and wait for them</text>')
    
    svg.append('</svg>')
    return "\n".join(svg)

svg_code = build_svg()
with open("test_candidate_job.svg", "w") as f:
    f.write(svg_code)
print("Saved test_candidate_job.svg")
