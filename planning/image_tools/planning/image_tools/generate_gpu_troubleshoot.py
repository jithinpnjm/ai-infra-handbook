import re
import xml.etree.ElementTree as ET

def build_svg():
    svg_lines = []
    svg_lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg_lines.append('  <title>GPU scheduling symptoms and first checks</title>')
    svg_lines.append('  <desc>Table symptom, likely cause, check</desc>')
    svg_lines.append('')
    svg_lines.append('  <!-- Canvas Background -->')
    svg_lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    svg_lines.append('')
    svg_lines.append('  <!-- Title: 48px bold -->')
    svg_lines.append('  <text x="800" y="58" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">GPU scheduling symptoms and first checks</text>')
    svg_lines.append('')
    svg_lines.append('  <!-- ==================== TABLE CONTAINER ==================== -->')
    svg_lines.append('  <!-- Outer boundary -->')
    svg_lines.append('  <rect x="40" y="85" width="1520" height="885" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg_lines.append('')
    svg_lines.append('  <!-- Table Header Background (main green) -->')
    svg_lines.append('  <path d="M 40 95 Q 40 85 50 85 L 1550 85 Q 1560 85 1560 95 L 1560 155 L 40 155 Z" fill="#207448" />')
    svg_lines.append('')
    svg_lines.append('  <!-- Header 1: symptom (Node 1) -->')
    svg_lines.append('  <g transform="translate(145, 96)" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <path d="M 12 36 L 24 10 L 36 36 Z" />')
    svg_lines.append('    <line x1="24" y1="18" x2="24" y2="26" />')
    svg_lines.append('    <circle cx="24" cy="31" r="1.5" fill="#ffffff" />')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="210" y="132" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#ffffff">symptom</text>')
    svg_lines.append('')
    svg_lines.append('  <!-- Header 2: likely cause (Node 2) -->')
    svg_lines.append('  <g transform="translate(635, 96)" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <circle cx="24" cy="24" r="9" />')
    svg_lines.append('    <path d="M 24 6 L 24 11 M 24 37 L 24 42 M 6 24 L 11 24 M 37 24 L 42 24 M 11.3 11.3 L 14.8 14.8 M 33.2 33.2 L 36.7 36.7 M 11.3 36.7 L 14.8 33.2 M 33.2 14.8 L 36.7 11.3" />')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="700" y="132" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#ffffff">likely cause</text>')
    svg_lines.append('')
    svg_lines.append('  <!-- Header 3: check (Node 3) -->')
    svg_lines.append('  <g transform="translate(1225, 96)" stroke="#ffffff" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <circle cx="22" cy="22" r="13" />')
    svg_lines.append('    <line x1="31" y1="31" x2="42" y2="42" />')
    svg_lines.append('    <polyline points="16,22 20,26 28,18" />')
    svg_lines.append('  </g>')
    svg_lines.append('  <text x="1290" y="132" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#ffffff">check</text>')
    svg_lines.append('')
    
    # Each cell has a list of line strings
    # Col 1: 30px bold (line height 34)
    # Col 2: 24px sans (line height 28)
    # Col 3: 24px mono (line height 28)
    row_defs = [
        # Row 1
        (["Invalid generic resource", "(gres) specification"],
         ["type or name not in", "GresTypes or node Gres"],
         ["scontrol show node, slurmd -G,", "typo in type"],
         85, "#ffffff", False),
        
        # Row 2
        (["Pending Resources or", "ReqNodeNotAvail"],
         ["request not satisfiable", "(type, count, memory per GPU,", "sockets with enforce-binding)", "or nodes drained"],
         ["scontrol show job,", "sinfo -o %N %G %t"],
         140, "#e8f1ea", False),
        
        # Row 3 (Orange highlight - single most important item)
        (["Node DRAIN gres/gpu", "count too low (0 &lt; 8)"],
         ["NVML or driver failed to load,", "GPU missing"],
         ["nvidia-smi, slurmd log,", "slurmd -G, dmesg Xid"],
         85, "#fff7f0", True),
        
        # Row 4
        (["CUDA_VISIBLE_DEVICES", "empty"],
         ["no File= or device constraint", "config, --gres not requested,", "--gpu-bind=none"],
         ["gres.conf,", "scontrol show job TresPerNode"],
         100, "#ffffff", False),
        
        # Row 5
        (["Job sees all GPUs"],
         ["ConstrainDevices=no"],
         ["cgroup.conf"],
         60, "#e8f1ea", False),
        
        # Row 6
        (["Two ranks use one GPU"],
         ["no per-task binding,", "--gpus-per-task missing,", "sharing configured"],
         ["gpu_env_check.py per rank"],
         100, "#ffffff", False),
        
        # Row 7
        (["Slow host-device copies"],
         ["CPUs on the wrong NUMA node"],
         ["--gres-flags=enforce-binding,", "Cores=, taskset,", "nvidia-smi topo -m"],
         100, "#e8f1ea", False),
        
        # Row 8
        (["NVLink-poor pairs", "allocated"],
         ["Links missing"],
         ["slurmd -G,", "--gres-flags=enforce-links"],
         70, "#ffffff", False),
        
        # Row 9
        (["MIG count wrong", "after reboot"],
         ["layout not recreated", "before slurmd"],
         ["systemd ordering,", "nvidia-smi -L"],
         75, "#e8f1ea", False),
    ]

    cur_y = 155
    for i, (sym_lines, cause_lines, chk_lines, r_h, bg, is_orange) in enumerate(row_defs, 1):
        svg_lines.append(f'  <!-- ==================== ROW {i} ==================== -->')
        # Row background
        svg_lines.append(f'  <rect x="40" y="{cur_y}" width="1520" height="{r_h}" fill="{bg}" />')
        
        if is_orange:
            # Single orange #db8129 accent on the most important row (Node DRAIN)
            svg_lines.append(f'  <rect x="40" y="{cur_y}" width="8" height="{r_h}" fill="#db8129" />')
        
        # Horizontal divider line after row (if not last)
        if i < len(row_defs):
            svg_lines.append(f'  <line x1="40" y1="{cur_y + r_h}" x2="1560" y2="{cur_y + r_h}" stroke="#207448" stroke-width="1" opacity="0.3" />')
        
        # Col 1: 30px bold, line spacing 34
        num_sym = len(sym_lines)
        sym_block_h = (num_sym - 1) * 34 + 24
        sym_start_y = cur_y + (r_h - sym_block_h) / 2 + 22
        sym_color = "#db8129" if is_orange else "#207448"
        
        svg_lines.append(f'  <text x="64" y="{sym_start_y:.1f}" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="{sym_color}">')
        for j, line_txt in enumerate(sym_lines):
            suffix = " " if j < num_sym - 1 else ""
            dy_val = 0 if j == 0 else 34
            svg_lines.append(f'    <tspan x="64" dy="{dy_val}">{line_txt}{suffix}</tspan>')
        svg_lines.append('  </text>')
        
        # Col 2: 24px sans, line spacing 28
        num_cause = len(cause_lines)
        cause_block_h = (num_cause - 1) * 28 + 18
        cause_start_y = cur_y + (r_h - cause_block_h) / 2 + 18
        
        svg_lines.append(f'  <text x="544" y="{cause_start_y:.1f}" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">')
        for j, line_txt in enumerate(cause_lines):
            suffix = " " if j < num_cause - 1 else ""
            dy_val = 0 if j == 0 else 28
            svg_lines.append(f'    <tspan x="544" dy="{dy_val}">{line_txt}{suffix}</tspan>')
        svg_lines.append('  </text>')

        # Col 3: 24px monospace, line spacing 28
        num_chk = len(chk_lines)
        chk_block_h = (num_chk - 1) * 28 + 18
        chk_start_y = cur_y + (r_h - chk_block_h) / 2 + 18
        
        svg_lines.append(f'  <text x="1064" y="{chk_start_y:.1f}" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
        for j, line_txt in enumerate(chk_lines):
            suffix = " " if j < num_chk - 1 else ""
            dy_val = 0 if j == 0 else 28
            svg_lines.append(f'    <tspan x="1064" dy="{dy_val}">{line_txt}{suffix}</tspan>')
        svg_lines.append('  </text>')
        svg_lines.append('')
        
        cur_y += r_h

    # Vertical column dividers
    svg_lines.append('  <!-- Vertical Column Dividers -->')
    svg_lines.append(f'  <line x1="520" y1="85" x2="520" y2="{cur_y}" stroke="#207448" stroke-width="1.5" opacity="0.4" />')
    svg_lines.append(f'  <line x1="1040" y1="85" x2="1040" y2="{cur_y}" stroke="#207448" stroke-width="1.5" opacity="0.4" />')
    svg_lines.append('')

    # Note container at bottom
    note_top = 1010
    note_h = 150
    svg_lines.append('  <!-- ==================== NOTE PANEL ==================== -->')
    svg_lines.append(f'  <rect x="40" y="{note_top}" width="1520" height="{note_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg_lines.append('')
    svg_lines.append('  <!-- Shield / Info Outline Icon (56px, stroke 4) -->')
    svg_lines.append(f'  <g transform="translate(68, {note_top + 47})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('    <path d="M 28 6 L 48 14 L 48 28 C 48 42 28 50 28 50 C 28 50 8 42 8 28 L 8 14 Z" />')
    svg_lines.append('    <line x1="28" y1="20" x2="28" y2="30" />')
    svg_lines.append('    <circle cx="28" cy="38" r="2" fill="#207448" />')
    svg_lines.append('  </g>')
    svg_lines.append('')
    svg_lines.append('  <!-- Note Text -->')
    svg_lines.append(f'  <text x="145" y="{note_top + 65}" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">')
    svg_lines.append('    <tspan x="145" dy="0">bring a recovered test node back with scontrol update NodeName=node[6-7] State=RESUME; </tspan>')
    svg_lines.append('    <tspan x="145" dy="38" font-family="system-ui, -apple-system, sans-serif">drain a node when a GPU reports Xid, ECC or NVLink faults</tspan>')
    svg_lines.append('  </text>')
    svg_lines.append('</svg>')

    return "\n".join(svg_lines)

svg_str = build_svg()
with open("planning/image_tools/candidate_gpu_troubleshoot.svg", "w", encoding="utf-8") as f:
    f.write(svg_str)
print("Updated candidate_gpu_troubleshoot.svg with proper dy values!")
