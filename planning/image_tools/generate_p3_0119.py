#!/usr/bin/env python3
import json
import re
import xml.etree.ElementTree as ET

def generate_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">')
    svg.append('  <title>Why a container ignores SIGTERM: PID 1 has no default signal actions</title>')
    svg.append('  <desc>Visual infographic explaining why PID 1 in a container ignores SIGTERM without a handler and comparing shell vs exec with the three PID 1 rules.</desc>')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129"/>')
    svg.append('    </marker>')
    svg.append('  </defs>')
    svg.append('  <!-- Canvas Background -->')
    svg.append('  <rect x="0" y="0" width="1600" height="1200" fill="#f5f8f5"/>')
    
    # 1. Title (48px bold)
    svg.append('  <!-- Title -->')
    svg.append('  <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Why a container ignores SIGTERM: </tspan>')
    svg.append('    <tspan x="800" dy="54">PID 1 has no default signal actions</tspan>')
    svg.append('  </text>')
    
    # Start trigger box on the left: 'docker stop or kubelet sends SIGTERM'
    # x = 40, y = 145, width = 240, height = 395
    svg.append('  <!-- Trigger Origin -->')
    svg.append('  <g id="trigger-origin">')
    svg.append('    <rect x="40" y="145" width="240" height="395" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    # Icon: gear / service (56px)
    svg.append('    <g transform="translate(132, 175)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="14"/>')
    svg.append('      <path d="M 28 6 L 28 14 M 28 42 L 28 50 M 6 28 L 14 28 M 42 28 L 50 28 M 12 12 L 18 18 M 38 38 L 44 44 M 12 44 L 18 38 M 38 18 L 44 12"/>')
    svg.append('    </g>')
    svg.append('    <text x="160" y="335" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('      <tspan x="160" dy="0">docker stop or </tspan>')
    svg.append('      <tspan x="160" dy="32">kubelet sends </tspan>')
    svg.append('      <tspan x="160" dy="32">SIGTERM</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Arrow from Trigger to Track 1
    svg.append('  <!-- Trigger to Track 1 -->')
    svg.append('  <line x1="280" y1="260" x2="325" y2="260" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)"/>')
    
    # Arrow from Trigger to Track 2
    svg.append('  <!-- Trigger to Track 2 -->')
    svg.append('  <line x1="280" y1="465" x2="325" y2="465" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)"/>')

    # ==========================================
    # TRACK 1 (Left timeline / Orange highlighted)
    # Header: Shell script as PID 1, no SIGTERM handler
    # ==========================================
    svg.append('  <!-- Track 1 Container -->')
    svg.append('  <g id="track-1">')
    svg.append('    <rect x="310" y="145" width="1250" height="195" rx="14" fill="#fff9f3" stroke="#db8129" stroke-width="3"/>')
    # Terminal / shell icon (32px)
    svg.append('    <g transform="translate(330, 156)" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="4" width="36" height="26" rx="4"/>')
    svg.append('      <polyline points="8,12 14,17 8,22"/>')
    svg.append('      <line x1="18" y1="22" x2="26" y2="22"/>')
    svg.append('    </g>')
    svg.append('    <text x="385" y="179" font-family="sans-serif" font-size="26" font-weight="bold" fill="#db8129">Shell script as PID 1, no SIGTERM handler</text>')
    
    # Box 1: PID 1 has no default action, so with no handler the signal is ignored
    # x = 325, y = 194, width = 330, height = 132
    svg.append('    <rect x="325" y="194" width="330" height="132" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2"/>')
    svg.append('    <text x="490" y="230" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="490" dy="0">PID 1 has no default </tspan>')
    svg.append('      <tspan x="490" dy="26">action, so with no </tspan>')
    svg.append('      <tspan x="490" dy="26">handler the signal </tspan>')
    svg.append('      <tspan x="490" dy="26">is ignored</tspan>')
    svg.append('    </text>')

    # Arrow 1 -> 2
    svg.append('    <line x1="655" y1="260" x2="680" y2="260" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)"/>')

    # Box 2: wait bar 'grace period, 30 seconds in Kubernetes by default'
    # x = 680, y = 194, width = 270, height = 132
    svg.append('    <rect x="680" y="194" width="270" height="132" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" stroke-dasharray="6 4"/>')
    svg.append('    <text x="815" y="230" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="815" dy="0">grace period, 30 </tspan>')
    svg.append('      <tspan x="815" dy="26">seconds in </tspan>')
    svg.append('      <tspan x="815" dy="26">Kubernetes </tspan>')
    svg.append('      <tspan x="815" dy="26">by default</tspan>')
    svg.append('    </text>')

    # Arrow 2 -> 3
    svg.append('    <line x1="950" y1="260" x2="975" y2="260" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)"/>')

    # Box 3: 'SIGKILL from the parent namespace'
    # x = 975, y = 194, width = 265, height = 132
    svg.append('    <rect x="975" y="194" width="265" height="132" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="1107.5" y="250" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1107.5" dy="0">SIGKILL from the </tspan>')
    svg.append('      <tspan x="1107.5" dy="32">parent namespace</tspan>')
    svg.append('    </text>')

    # Arrow 3 -> 4
    svg.append('    <line x1="1240" y1="260" x2="1265" y2="260" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)"/>')

    # Box 4: outcome box 'training job loses its chance to checkpoint'
    # x = 1265, y = 194, width = 295, height = 132
    svg.append('    <rect x="1265" y="194" width="295" height="132" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="1412.5" y="240" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1412.5" dy="0">training job loses </tspan>')
    svg.append('      <tspan x="1412.5" dy="30">its chance to </tspan>')
    svg.append('      <tspan x="1412.5" dy="30">checkpoint</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==========================================
    # TRACK 2 (Right timeline / Green)
    # Header: exec python train.py (the program is PID 1 and installs its own handler)
    # ==========================================
    svg.append('  <!-- Track 2 Container -->')
    svg.append('  <g id="track-2">')
    svg.append('    <rect x="310" y="355" width="1250" height="185" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>')
    # Code execution icon (32px)
    svg.append('    <g transform="translate(330, 366)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="18" cy="18" r="14"/>')
    svg.append('      <polygon points="14,11 26,18 14,25" fill="#207448"/>')
    svg.append('    </g>')
    svg.append('    <text x="385" y="389" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">exec python train.py (the program is PID 1 and installs its own handler)</text>')

    # Box 1: 'handler runs'
    # x = 325, y = 405, width = 340, height = 120
    svg.append('    <rect x="325" y="405" width="340" height="120" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="495" y="472" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">handler runs</text>')

    # Arrow 1 -> 2
    svg.append('    <line x1="665" y1="465" x2="740" y2="465" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)"/>')

    # Box 2: 'checkpoint written'
    # x = 740, y = 405, width = 400, height = 120
    svg.append('    <rect x="740" y="405" width="400" height="120" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="940" y="472" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">checkpoint written</text>')

    # Arrow 2 -> 3
    svg.append('    <line x1="1140" y1="465" x2="1215" y2="465" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)"/>')

    # Box 3: 'clean exit'
    # x = 1215, y = 405, width = 345, height = 120
    svg.append('    <rect x="1215" y="405" width="345" height="120" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    svg.append('    <text x="1387.5" y="472" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">clean exit</text>')
    svg.append('  </g>')

    # ==========================================
    # THREE PID 1 RULES (Below, three-card strip)
    # Header: The three PID 1 rules
    # ==========================================
    svg.append('  <!-- Three PID 1 Rules Header -->')
    svg.append('  <text x="800" y="580" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">The three PID 1 rules</text>')

    # Card 1:
    # 'Signals: from inside the namespace a signal reaches PID 1 only if it installed a handler; SIGKILL and SIGSTOP from inside are ignored; from the parent namespace they still work'
    # x = 40, y = 610, width = 480, height = 310
    svg.append('  <!-- Card 1 -->')
    svg.append('  <g id="card-1">')
    svg.append('    <rect x="40" y="610" width="480" height="310" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Icon: Shield / Signals (56px)
    svg.append('    <g transform="translate(65, 625)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 48 14 V 28 C 48 40 28 48 28 48 C 28 48 8 40 8 28 V 14 Z"/>')
    svg.append('    </g>')
    svg.append('    <text x="65" y="700" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="65" dy="0">Signals: from inside the </tspan>')
    svg.append('      <tspan x="65" dy="28">namespace a signal reaches </tspan>')
    svg.append('      <tspan x="65" dy="28">PID 1 only if it installed </tspan>')
    svg.append('      <tspan x="65" dy="28">a handler; SIGKILL and </tspan>')
    svg.append('      <tspan x="65" dy="28">SIGSTOP from inside are </tspan>')
    svg.append('      <tspan x="65" dy="28">ignored; from the parent </tspan>')
    svg.append('      <tspan x="65" dy="28">namespace they still work</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Card 2:
    # 'Zombies: orphans are re-parented to PID 1, which must call wait(); otherwise zombies pile up and can exhaust pids.max'
    # x = 560, y = 610, width = 480, height = 310
    svg.append('  <!-- Card 2 -->')
    svg.append('  <g id="card-2">')
    svg.append('    <rect x="560" y="610" width="480" height="310" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Icon: CPU / Reaping / Stack (56px)
    svg.append('    <g transform="translate(585, 625)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="10" y="10" width="36" height="36" rx="4"/>')
    svg.append('      <line x1="18" y1="22" x2="38" y2="22"/>')
    svg.append('      <line x1="18" y1="34" x2="30" y2="34"/>')
    svg.append('    </g>')
    svg.append('    <text x="585" y="715" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="585" dy="0">Zombies: orphans are </tspan>')
    svg.append('      <tspan x="585" dy="32">re-parented to PID 1, </tspan>')
    svg.append('      <tspan x="585" dy="32">which must call wait(); </tspan>')
    svg.append('      <tspan x="585" dy="32">otherwise zombies pile up </tspan>')
    svg.append('      <tspan x="585" dy="32">and can exhaust pids.max</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Card 3:
    # 'When PID 1 exits the kernel kills every other process in the namespace with SIGKILL, which is why a container dies when its main process dies'
    # x = 1080, y = 610, width = 480, height = 310
    svg.append('  <!-- Card 3 -->')
    svg.append('  <g id="card-3">')
    svg.append('    <rect x="1080" y="610" width="480" height="310" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>')
    # Icon: Application / Window / Process (56px)
    svg.append('    <g transform="translate(1105, 625)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="8" y="10" width="40" height="36" rx="4"/>')
    svg.append('      <line x1="8" y1="22" x2="48" y2="22"/>')
    svg.append('      <circle cx="16" cy="16" r="2" fill="#207448"/>')
    svg.append('      <circle cx="24" cy="16" r="2" fill="#207448"/>')
    svg.append('    </g>')
    svg.append('    <text x="1105" y="700" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1105" dy="0">When PID 1 exits the </tspan>')
    svg.append('      <tspan x="1105" dy="32">kernel kills every other </tspan>')
    svg.append('      <tspan x="1105" dy="32">process in the namespace </tspan>')
    svg.append('      <tspan x="1105" dy="32">with SIGKILL, which is why </tspan>')
    svg.append('      <tspan x="1105" dy="32">a container dies when its </tspan>')
    svg.append('      <tspan x="1105" dy="32">main process dies</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==========================================
    # FIX STRIP
    # 'exec in the entrypoint; tini; docker run --init; dumb-init; Kubernetes shareProcessNamespace; exec form ["python","train.py"] not the shell form'
    # ==========================================
    svg.append('  <!-- Fix Strip -->')
    svg.append('  <g id="fix-strip">')
    svg.append('    <rect x="40" y="940" width="1520" height="110" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Disk cylinder / storage / tool icon (56px)
    svg.append('    <g transform="translate(65, 967)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <ellipse cx="28" cy="14" rx="20" ry="8"/>')
    svg.append('      <path d="M 8 14 V 42 C 8 46 17 50 28 50 C 39 50 48 46 48 42 V 14"/>')
    svg.append('      <path d="M 8 28 C 8 32 17 36 28 36 C 39 36 48 32 48 28"/>')
    svg.append('    </g>')
    svg.append('    <text x="135" y="985" font-family="monospace" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0">exec in the entrypoint; tini; docker run --init; dumb-init; </tspan>')
    svg.append('      <tspan x="135" dy="34">Kubernetes shareProcessNamespace; exec form ["python","train.py"] not the shell form</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==========================================
    # BOTTOM BAR (Takeaway)
    # 'End the script with exec so the program becomes PID 1'
    # ==========================================
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1075" width="1520" height="90" rx="14" fill="#207448"/>')
    svg.append('    <text x="800" y="1130" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">End the script with exec so the program becomes PID 1</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

if __name__ == "__main__":
    content = generate_svg()
    with open("candidate_p3_0119.svg", "w") as f:
        f.write(content)
    print("Regenerated candidate_p3_0119.svg.")
