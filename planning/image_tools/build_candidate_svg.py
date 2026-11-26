def build_svg():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>What the canary host sees in the driver-tuning play</title>')
    svg.append('  <desc>Timeline of the canary host gpu001 through Slurm drain pre-task, driver configuration tasks, handler reload, validation, and rollout gate.</desc>')
    svg.append('  <defs>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    
    # Title: 48px bold
    svg.append('  <text x="800" y="50" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">What the canary host sees in the driver-tuning play</text>')

    # ==================== CARD 1: STORY STRIP (y=72..168, h=96) ====================
    svg.append('  <!-- Story strip -->')
    svg.append('  <g id="story-strip">')
    svg.append('    <rect x="40" y="72" width="1520" height="96" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Warning triangle outline icon (56x56)
    svg.append('    <g transform="translate(65, 92)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="28,6 52,48 4,48" />')
    svg.append('      <line x1="28" y1="22" x2="28" y2="34" />')
    svg.append('      <circle cx="28" cy="41" r="2" fill="#207448" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="110" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">if the parameter is wrong for one hardware model, every node of that model fails together </tspan>')
    svg.append('      <tspan x="145" dy="34">and the Slurm queue fills with failed jobs before anyone reads the first alert</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== CARD 2: PLAY CONFIGURATION (y=178..242, h=64) ====================
    svg.append('  <!-- Play configuration card -->')
    svg.append('  <g id="play-config">')
    svg.append('    <rect x="40" y="178" width="1520" height="64" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Settings sliders outline icon (56x40)
    svg.append('    <g transform="translate(68, 190)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="4" y1="12" x2="48" y2="12" />')
    svg.append('      <circle cx="16" cy="12" r="5" fill="#ffffff" />')
    svg.append('      <line x1="4" y1="28" x2="48" y2="28" />')
    svg.append('      <circle cx="36" cy="28" r="5" fill="#ffffff" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="217" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">serial [1, 10%, 100%], max_fail_percentage 5, expected_gpus 8</text>')
    svg.append('  </g>')

    # ==================== CARD 3: PRE-STEP (y=252..316, h=64) ====================
    svg.append('  <!-- Pre-step -->')
    svg.append('  <g id="pre-step">')
    svg.append('    <rect x="40" y="252" width="1520" height="64" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Magnifying glass / diff check icon (44x44)
    svg.append('    <g transform="translate(71, 262)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="18" cy="18" r="13" />')
    svg.append('      <line x1="28" y1="28" x2="42" y2="42" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="291" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">run --check --diff --limit gpu001 first</text>')
    svg.append('  </g>')

    # Vector number paths for white numbers inside circles
    def num1_path(cx, cy):
        return f'<path d="M {cx-4} {cy-7} L {cx+2} {cy-12} L {cx+2} {cy+12} M {cx-7} {cy+12} L {cx+11} {cy+12}" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />'

    def num2_path(cx, cy):
        return f'<path d="M {cx-9} {cy-7} C {cx-9} {cy-13} {cx+9} {cy-13} {cx+9} {cy-5} C {cx+9} {cy+1} {cx-8} {cy+6} {cx-9} {cy+12} L {cx+10} {cy+12}" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />'

    def num3_path(cx, cy):
        return f'<path d="M {cx-8} {cy-11} L {cx+8} {cy-11} L {cx} {cy-2} C {cx+7} {cy-2} {cx+9} {cy+4} {cx+9} {cy+7} C {cx+9} {cy+12} {cx-1} {cy+13} {cx-8} {cy+10}" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />'

    def num4_path(cx, cy):
        return f'<path d="M {cx+3} {cy+12} L {cx+3} {cy-12} L {cx-9} {cy+4} L {cx+9} {cy+4}" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />'

    def num5_path(cx, cy):
        return f'<path d="M {cx+7} {cy-11} L {cx-7} {cy-11} L {cx-7} {cy-1} C {cx-7} {cy-1} {cx+8} {cy-1} {cx+8} {cy+6} C {cx+8} {cy+12} {cx-2} {cy+13} {cx-8} {cy+10}" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />'

    # ==================== CARD 4: STEP 1 (y=326..422, h=96) - ORANGE ====================
    svg.append('  <!-- Step 1: Pre-task DRAIN check (Orange accent) -->')
    svg.append('  <g id="step-1">')
    svg.append('    <rect x="40" y="326" width="1520" height="96" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    # Orange number circle 1 (r=24)
    svg.append('    <circle cx="93" cy="374" r="24" fill="#db8129" />')
    svg.append(f'    {num1_path(93, 374)}')
    svg.append('    <text x="145" y="364" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">pre_task: delegate to the first slurm_controller host: scontrol show node gpu001, </tspan>')
    svg.append('      <tspan x="145" dy="34">check_mode false, changed_when false, failed_when DRAIN not in node_state.stdout</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== CARD 5: STEP 2 (y=432..496, h=64) ====================
    svg.append('  <!-- Step 2: sysctl vm.swappiness -->')
    svg.append('  <g id="step-2">')
    svg.append('    <rect x="40" y="432" width="1520" height="64" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Green number circle 2 (r=24)
    svg.append('    <circle cx="93" cy="464" r="24" fill="#207448" />')
    svg.append(f'    {num2_path(93, 464)}')
    svg.append('    <text x="145" y="471" font-family="monospace" font-size="24" fill="#303a36">sysctl: vm.swappiness = 1 persisted in /etc/sysctl.d/90-ai.conf, reload true</text>')
    svg.append('  </g>')

    # ==================== CARD 6: STEP 3 (y=506..636, h=130) ====================
    svg.append('  <!-- Step 3: template override.conf -->')
    svg.append('  <g id="step-3">')
    svg.append('    <rect x="40" y="506" width="1520" height="130" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Green number circle 3 (r=24)
    svg.append('    <circle cx="93" cy="571" r="24" fill="#207448" />')
    svg.append(f'    {num3_path(93, 571)}')
    svg.append('    <text x="145" y="544" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">template: nvidia-persistenced.override.conf.j2 to </tspan>')
    svg.append('      <tspan x="145" dy="34">/etc/systemd/system/nvidia-persistenced.service.d/override.conf </tspan>')
    svg.append('      <tspan x="145" dy="34">mode 0644, notify Restart persistenced</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== CARD 7: STEP 4 (y=646..710, h=64) ====================
    svg.append('  <!-- Step 4: restart persistenced handler -->')
    svg.append('  <g id="step-4">')
    svg.append('    <rect x="40" y="646" width="1520" height="64" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Green number circle 4 (r=24)
    svg.append('    <circle cx="93" cy="678" r="24" fill="#207448" />')
    svg.append(f'    {num4_path(93, 678)}')
    svg.append('    <text x="145" y="685" font-family="monospace" font-size="24" fill="#303a36">handler: restart nvidia-persistenced with daemon_reload, only if the template changed</text>')
    svg.append('  </g>')

    # ==================== CARD 8: STEP 5 (y=720..816, h=96) ====================
    svg.append('  <!-- Step 5: nvidia-smi validation -->')
    svg.append('  <g id="step-5">')
    svg.append('    <rect x="40" y="720" width="1520" height="96" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Green number circle 5 (r=24)
    svg.append('    <circle cx="93" cy="768" r="24" fill="#207448" />')
    svg.append(f'    {num5_path(93, 768)}')
    svg.append('    <text x="145" y="758" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">post_task: nvidia-smi --query-gpu=index --format=csv,noheader; </tspan>')
    svg.append('      <tspan x="145" dy="34">failed_when stdout_lines length != expected_gpus</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== CARD 9: GATE (y=826..922, h=96) ====================
    svg.append('  <!-- Validation Gate -->')
    svg.append('  <g id="gate">')
    svg.append('    <rect x="40" y="826" width="1520" height="96" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    # Barrier / gate outline icon (56x56)
    svg.append('    <g transform="translate(65, 846)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="40" rx="4" />')
    svg.append('      <line x1="6" y1="20" x2="50" y2="20" />')
    svg.append('      <line x1="6" y1="36" x2="50" y2="36" />')
    svg.append('      <circle cx="28" cy="28" r="4" fill="#207448" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="864" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">validation failure stops the play before the 10 percent batch </tspan>')
    svg.append('      <tspan x="145" dy="34">because of max_fail_percentage</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== CARD 10: STRIP RESUME (y=932..996, h=64) ====================
    svg.append('  <!-- Strip: Resume Slurm nodes -->')
    svg.append('  <g id="strip-resume">')
    svg.append('    <rect x="40" y="932" width="1520" height="64" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Return to service checkmark circle icon (44x44)
    svg.append('    <g transform="translate(71, 942)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="22" cy="22" r="18" />')
    svg.append('      <polyline points="14,22 20,28 30,16" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="971" font-family="sans-serif" font-size="24" fill="#303a36">resume the Slurm nodes in a separate, explicit play once validation has passed</text>')
    svg.append('  </g>')

    # ==================== CARD 11: BOTTOM TAKEAWAY BAR (y=1090..1160, h=70) ====================
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1090" width="1520" height="70" rx="14" fill="#207448" />')
    svg.append('    <text x="800" y="1134" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Apply in small batches and validate each node as it goes</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

svg_text = build_svg()
with open("test_canary_candidate.svg", "w") as f:
    f.write(svg_text)
print("Saved perfectly tuned test_canary_candidate.svg!")
