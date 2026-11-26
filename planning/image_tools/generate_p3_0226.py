#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

def generate_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>Handshake outcomes: a missing SYN-ACK, a reset, or a repeating SYN</title>')
    svg.append('  <desc>Visual explanation of TCP handshake outcomes: healthy three-way handshake, connection reset from a closed port, and silence from packet drops with server-side capture diagnostics.</desc>')
    svg.append('')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    svg.append('')
    svg.append('  <!-- Canvas Background -->')
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    svg.append('')
    svg.append('  <!-- Title (48px bold) -->')
    svg.append('  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Handshake outcomes: a missing SYN-ACK, a reset, or a repeating SYN</text>')
    svg.append('')

    # =========================================================================
    # LADDER A: Healthy
    # =========================================================================
    # Panel A: x=40, y=100, w=480, h=580
    svg.append('  <!-- ==================== LADDER A: Healthy ==================== -->')
    svg.append('  <g id="ladder-a">')
    svg.append('    <rect x="40" y="100" width="480" height="580" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('')
    # Icon for Healthy: Shield with checkmark (56px) at (65, 118)
    svg.append('    <!-- Shield / Health Icon (56px) -->')
    svg.append('    <g transform="translate(65, 118)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 50 14 V 28 C 50 42 28 50 28 50 C 28 50 6 42 6 28 V 14 Z" />')
    svg.append('      <polyline points="18,27 25,34 38,20" />')
    svg.append('    </g>')
    # Title: Healthy (32px bold) at (135, 156)
    svg.append('    <text x="135" y="156" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Healthy</text>')
    svg.append('')
    # Swimlane vertical lifelines: client left (x=105), server right (x=455)
    svg.append('    <!-- Client and Server Lifelines -->')
    svg.append('    <circle cx="105" cy="205" r="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="455" cy="205" r="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <line x1="105" y1="219" x2="105" y2="650" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 6" />')
    svg.append('    <line x1="455" y1="219" x2="455" y2="650" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 6" />')
    svg.append('')

    # Message 1: SYN with options MSS, SACK permitted, timestamps, window scale
    # Box: x=65, y=235, w=350, h=150
    # Arrow 1 from client (105, 395) to server (437, 395)
    svg.append('    <!-- Arrow 1: SYN with options -->')
    svg.append('    <rect x="65" y="235" width="350" height="150" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="240" y="267" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="240" dy="0">SYN with options MSS,</tspan>')
    svg.append('      <tspan x="240" dy="32">SACK permitted,</tspan>')
    svg.append('      <tspan x="240" dy="32">timestamps, window</tspan>')
    svg.append('      <tspan x="240" dy="32">scale</tspan>')
    svg.append('    </text>')
    svg.append('    <line x1="105" y1="395" x2="437" y2="395" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('')

    # Message 2: SYN-ACK
    # Arrow 2 from server (455, 490) to client (123, 490)
    # Box sitting on/above arrow: x=175, y=468, w=150, h=44
    svg.append('    <!-- Arrow 2: SYN-ACK -->')
    svg.append('    <line x1="455" y1="490" x2="123" y2="490" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('    <rect x="175" y="468" width="150" height="44" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="250" y="499" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">SYN-ACK</text>')
    svg.append('')

    # Message 3: ACK
    # Arrow 3 from client (105, 580) to server (437, 580)
    # Box sitting on/above arrow: x=195, y=558, w=110, h=44
    svg.append('    <!-- Arrow 3: ACK -->')
    svg.append('    <line x1="105" y1="580" x2="437" y2="580" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('    <rect x="195" y="558" width="110" height="44" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="250" y="589" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">ACK</text>')
    svg.append('  </g>')
    svg.append('')

    # =========================================================================
    # LADDER B: Reset
    # =========================================================================
    # Panel B: x=560, y=100, w=480, h=580
    svg.append('  <!-- ==================== LADDER B: Reset ==================== -->')
    svg.append('  <g id="ladder-b">')
    svg.append('    <rect x="560" y="100" width="480" height="580" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('')
    # Icon for Reset: Octagon / Closed port lock (56px) at (585, 118)
    svg.append('    <!-- Closed Port / Refusal Icon (56px) -->')
    svg.append('    <g transform="translate(585, 118)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="22" />')
    svg.append('      <line x1="12" y1="28" x2="44" y2="28" />')
    svg.append('    </g>')
    # Title: Reset (32px bold) at (655, 156)
    svg.append('    <text x="655" y="156" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Reset</text>')
    svg.append('')
    # Swimlane vertical lifelines: client left (x=625), server right (x=975)
    svg.append('    <!-- Client and Server Lifelines -->')
    svg.append('    <circle cx="625" cy="205" r="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="975" cy="205" r="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <line x1="625" y1="219" x2="625" y2="470" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 6" />')
    svg.append('    <line x1="975" y1="219" x2="975" y2="470" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 6" />')
    svg.append('')

    # Message 1: SYN
    # Arrow 4 from client (625, 290) to server (957, 290)
    svg.append('    <!-- Arrow 4: SYN -->')
    svg.append('    <line x1="625" y1="290" x2="957" y2="290" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('    <rect x="745" y="268" width="110" height="44" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="800" y="299" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">SYN</text>')
    svg.append('')

    # Message 2: RST (from server to client)
    # Arrow 5 from server (975, 395) to client (643, 395)
    svg.append('    <!-- Arrow 5: RST -->')
    svg.append('    <line x1="975" y1="395" x2="643" y2="395" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('    <rect x="745" y="373" width="110" height="44" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="800" y="404" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">RST</text>')
    svg.append('')

    # Card: a reset means someone is refusing you; usually the port is closed
    # x=600, y=500, w=400, h=130
    svg.append('    <!-- Card: a reset means someone is refusing you -->')
    svg.append('    <rect x="600" y="500" width="400" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="800" y="542" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="800" dy="0">a reset means someone is</tspan>')
    svg.append('      <tspan x="800" dy="34">refusing you; usually</tspan>')
    svg.append('      <tspan x="800" dy="34">the port is closed</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # =========================================================================
    # LADDER C: Silence (orange)
    # =========================================================================
    # Panel C: x=1080, y=100, w=480, h=580
    # Highlighted with single orange #db8129 stroke
    svg.append('  <!-- ==================== LADDER C: Silence (orange) ==================== -->')
    svg.append('  <g id="ladder-c">')
    svg.append('    <rect x="1080" y="100" width="480" height="580" rx="16" fill="#e8f1ea" stroke="#db8129" stroke-width="4" />')
    svg.append('')
    # Icon for Silence: Mute speaker / sound-off (56px) at (1105, 118)
    svg.append('    <!-- Silence / Sound-off Icon (56px) -->')
    svg.append('    <g transform="translate(1105, 118)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="6,20 18,20 32,10 32,46 18,36 6,36" />')
    svg.append('      <line x1="40" y1="20" x2="52" y2="36" />')
    svg.append('      <line x1="52" y1="20" x2="40" y2="36" />')
    svg.append('    </g>')
    # Title: Silence (32px bold) at (1175, 156)
    svg.append('    <text x="1175" y="156" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Silence</text>')
    svg.append('')
    # Swimlane vertical lifelines: client left (x=1145), server right (x=1495)
    svg.append('    <!-- Client and Server Lifelines -->')
    svg.append('    <circle cx="1145" cy="205" r="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <circle cx="1495" cy="205" r="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <line x1="1145" y1="219" x2="1145" y2="470" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 6" />')
    svg.append('    <line x1="1495" y1="219" x2="1495" y2="470" stroke="#207448" stroke-width="2.5" stroke-dasharray="6 6" />')
    svg.append('')

    # Messages: SYN, then the same SYN repeated, each a little later
    # Arrow 6: initial SYN from client (1145, 275) to server (1477, 275)
    svg.append('    <!-- Arrow 6: initial SYN -->')
    svg.append('    <line x1="1145" y1="275" x2="1477" y2="275" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('')
    # Arrow 7: repeated SYN from client (1145, 415) to server (1477, 415)
    svg.append('    <!-- Arrow 7: repeated SYN -->')
    svg.append('    <line x1="1145" y1="415" x2="1477" y2="415" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    svg.append('')
    # Message label card spanning between the two arrows: x=1160, y=295, w=320, h=100
    svg.append('    <!-- Label for repeating SYN -->')
    svg.append('    <rect x="1160" y="295" width="320" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1320" y="327" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1320" dy="0">SYN, then the same</tspan>')
    svg.append('      <tspan x="1320" dy="30">SYN repeated, each</tspan>')
    svg.append('      <tspan x="1320" dy="30">a little later</tspan>')
    svg.append('    </text>')
    svg.append('')

    # Card: silence means someone is ignoring you: a drop, a block or a missing route
    # x=1120, y=500, w=400, h=130
    svg.append('    <!-- Card: silence means someone is ignoring you -->')
    svg.append('    <rect x="1120" y="500" width="400" height="130" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1320" y="542" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1320" dy="0">silence means someone is</tspan>')
    svg.append('      <tspan x="1320" dy="34">ignoring you: a drop, a</tspan>')
    svg.append('      <tspan x="1320" dy="34">block or a missing route</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # =========================================================================
    # LOWER ROW: Extra strip (left: x=40..1040, w=1000) & Branching check (right: x=1080..1560, w=480)
    # y=710 to y=1060 (h=350)
    # =========================================================================

    # Extra strip on left:
    # Options: one SYN with window scale and the other without suggests a middlebox stripping options; throughput then limited to 64 KB per RTT. Fix belongs to the middlebox, not the application
    svg.append('  <!-- ==================== EXTRA STRIP ==================== -->')
    svg.append('  <g id="extra-strip">')
    svg.append('    <rect x="40" y="710" width="1000" height="350" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Icon for middlebox / options: Sliders / Filter (56px) at (65, 745)
    svg.append('    <!-- Middlebox / Filter Icon (56px) -->')
    svg.append('    <g transform="translate(65, 745)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="8" y1="16" x2="48" y2="16" />')
    svg.append('      <circle cx="20" cy="16" r="6" fill="#ffffff" />')
    svg.append('      <line x1="8" y1="36" x2="48" y2="36" />')
    svg.append('      <circle cx="36" cy="36" r="6" fill="#ffffff" />')
    svg.append('    </g>')
    svg.append('    <rect x="140" y="725" width="875" height="320" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="577" y="800" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="577" dy="0">Options: one SYN with window scale and the other without</tspan>')
    svg.append('      <tspan x="577" dy="44">suggests a middlebox stripping options; throughput then</tspan>')
    svg.append('      <tspan x="577" dy="44">limited to 64 KB per RTT. Fix belongs to the middlebox,</tspan>')
    svg.append('      <tspan x="577" dy="44">not the application</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Branching check under C:
    # Check the server's capture next: SYN there but no SYN-ACK leaves = the server or a firewall in front of it is ignoring the port; SYN never appears on the server = the path between the two hosts is the suspect
    svg.append('  <!-- ==================== BRANCHING CHECK UNDER C ==================== -->')
    svg.append('  <g id="branching-check">')
    svg.append('    <rect x="1080" y="710" width="480" height="350" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <rect x="1100" y="725" width="440" height="320" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1320" y="774" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1320" dy="0">Check the server\'s</tspan>')
    svg.append('      <tspan x="1320" dy="28">capture next: SYN there</tspan>')
    svg.append('      <tspan x="1320" dy="28">but no SYN-ACK leaves =</tspan>')
    svg.append('      <tspan x="1320" dy="28">the server or a firewall</tspan>')
    svg.append('      <tspan x="1320" dy="28">in front of it is</tspan>')
    svg.append('      <tspan x="1320" dy="28">ignoring the port;</tspan>')
    svg.append('      <tspan x="1320" dy="28">SYN never appears on</tspan>')
    svg.append('      <tspan x="1320" dy="28">the server = the path</tspan>')
    svg.append('      <tspan x="1320" dy="28">between the two hosts</tspan>')
    svg.append('      <tspan x="1320" dy="28">is the suspect</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # =========================================================================
    # BOTTOM TAKEAWAY BAR
    # =========================================================================
    # x=40, y=1090, w=1520, h=70
    svg.append('  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1090" width="1520" height="70" rx="14" fill="#207448" />')
    svg.append('    <text x="800" y="1134" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Silence means ignored, a reset means refused</text>')
    svg.append('  </g>')
    svg.append('</svg>')
    
    return '\n'.join(svg)

if __name__ == '__main__':
    content = generate_svg()
    pathlib.Path('test_candidate_p3_0226.svg').write_text(content)
    print('Generated test_candidate_p3_0226.svg successfully!')
