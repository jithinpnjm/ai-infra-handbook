import pathlib
import xml.etree.ElementTree as ET
import re

def build_svg():
    W = 1600
    H = 1180

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>The two queues behind listen(): where a busy server drops connections</title>')
    svg.append('  <desc>Visual explanation of the SYN queue and Accept queue in Linux TCP listen(), packet flow, failure callouts, and fixes.</desc>')

    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">')
    svg.append('      <path d="M 0 1 L 10 5 L 0 9 z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect x="0" y="0" width="{W}" height="{H}" fill="#f5f8f5" />')

    # Title: 48px bold
    svg.append('  <text x="50" y="60" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="50" dy="0">The two queues behind listen():</tspan>')
    svg.append('    <tspan x="50" dy="54">where a busy server drops connections</tspan>')
    svg.append('  </text>')

    # Client Box (x: 50..170, y: 150..710) - outline icon representing Client
    svg.append('  <rect x="50" y="150" width="120" height="560" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Client visual icon (workstation / laptop)
    # Monitor screen
    svg.append('  <rect x="75" y="380" width="70" height="50" rx="6" fill="#ffffff" stroke="#207448" stroke-width="4" />')
    svg.append('  <line x1="85" y1="395" x2="135" y2="395" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    svg.append('  <line x1="85" y1="410" x2="115" y2="410" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    # Monitor stand
    svg.append('  <line x1="110" y1="430" x2="110" y2="450" stroke="#207448" stroke-width="4" stroke-linecap="round" />')
    svg.append('  <line x1="90" y1="450" x2="130" y2="450" stroke="#207448" stroke-width="4" stroke-linecap="round" />')

    # Handshake Arrows between Client and Server
    # Arrow 1: SYN (left-to-right)
    svg.append('  <line x1="170" y1="190" x2="300" y2="190" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('  <text x="235" y="180" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">SYN</text>')

    # Arrow 2: SYN-ACK (right-to-left)
    svg.append('  <line x1="300" y1="240" x2="170" y2="240" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('  <text x="235" y="230" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">SYN-ACK</text>')

    # Arrow 3: ACK (left-to-right)
    svg.append('  <line x1="170" y1="630" x2="300" y2="630" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('  <text x="235" y="620" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">ACK</text>')

    # Server container border (subtle container background)
    svg.append('  <rect x="290" y="140" width="770" height="910" rx="20" fill="none" stroke="#207448" stroke-width="1.5" stroke-dasharray="8 6" opacity="0.4" />')

    # Node 1: SYN queue box (x: 300..1050, y: 150..280)
    svg.append('  <rect x="300" y="150" width="750" height="130" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # Icon for SYN queue: queue slots / buffer (56px)
    svg.append('  <g transform="translate(320, 187)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    svg.append('    <line x1="18" y1="12" x2="18" y2="44" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    svg.append('    <line x1="36" y1="12" x2="36" y2="44" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    svg.append('    <circle cx="9" cy="28" r="4" fill="#207448" />')
    svg.append('    <circle cx="27" cy="28" r="4" fill="#207448" />')
    svg.append('  </g>')
    # Text for SYN queue
    svg.append('  <text x="395" y="202" font-family="sans-serif" font-size="28" fill="#303a36">')
    svg.append('    <tspan x="395" dy="0" font-weight="bold">SYN queue: half-open connections,</tspan>')
    svg.append('    <tspan x="395" dy="42" font-family="monospace" font-size="24">size set by tcp_max_syn_backlog</tspan>')
    svg.append('  </text>')

    # Callout 2: on the SYN queue (x: 300..1050, y: 310..520)
    svg.append('  <rect x="300" y="310" width="750" height="210" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon for Callout 2: ticket / shield (56px)
    svg.append('  <g transform="translate(320, 387)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <path d="M 12 28 Q 28 14 44 28 Q 28 48 12 28 Z" fill="none" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="28" cy="28" r="5" fill="#207448" />')
    svg.append('  </g>')
    # Text for Callout 2
    svg.append('  <text x="395" y="344" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="395" dy="0" font-weight="bold">SYN flood or sudden burst fills it; fix with</tspan>')
    svg.append('    <tspan x="395" dy="28" font-family="monospace">net.ipv4.tcp_syncookies=1: </tspan><tspan font-family="sans-serif">the kernel</tspan>')
    svg.append('    <tspan x="395" dy="28">encodes the connection state in the SYN-ACK</tspan>')
    svg.append('    <tspan x="395" dy="28">sequence number, so no queue entry is needed,</tspan>')
    svg.append('    <tspan x="395" dy="28">at the cost of losing some options</tspan>')
    svg.append('    <tspan x="395" dy="28">(a clinic that hands each visitor a ticket</tspan>')
    svg.append('    <tspan x="395" dy="28">instead of keeping a waiting list)</tspan>')
    svg.append('  </text>')

    # Node 2: Accept queue box (x: 300..740, y: 550..710)
    svg.append('  <rect x="300" y="550" width="440" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # Icon for Accept queue: queue with checkmarks
    svg.append('  <g transform="translate(315, 602)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    svg.append('    <path d="M 14 28 L 24 38 L 42 18" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />')
    svg.append('  </g>')
    # Text for Accept queue
    svg.append('  <text x="385" y="586" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('    <tspan x="385" dy="0" font-weight="bold">Accept queue:</tspan>')
    svg.append('    <tspan x="385" dy="30" font-size="24">completed handshakes</tspan>')
    svg.append('    <tspan x="385" dy="28" font-size="24">waiting for accept(),</tspan>')
    svg.append('    <tspan x="385" dy="30" font-family="monospace" font-size="24">size min(backlog,</tspan>')
    svg.append('    <tspan x="385" dy="28" font-family="monospace" font-size="24">net.core.somaxconn)</tspan>')
    svg.append('  </text>')

    # Arrow 4: from Accept queue to application accept() loop
    svg.append('  <line x1="740" y1="630" x2="800" y2="630" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')

    # Node 3: application accept() loop (x: 800..1050, y: 550..710)
    svg.append('  <rect x="800" y="550" width="250" height="160" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Icon for application accept() loop: gear / loop (56px)
    svg.append('  <g transform="translate(897, 570)">')
    svg.append('    <circle cx="28" cy="28" r="20" fill="none" stroke="#207448" stroke-width="3" stroke-dasharray="14 5" />')
    svg.append('    <circle cx="28" cy="28" r="9" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('  </g>')
    # Text for application accept() loop
    svg.append('  <text x="925" y="660" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="925" dy="0">application</tspan>')
    svg.append('    <tspan x="925" dy="32">accept() loop</tspan>')
    svg.append('  </text>')

    # Callout 1 (orange): on the accept queue (x: 300..1050, y: 740..1020)
    svg.append('  <rect x="300" y="740" width="750" height="280" rx="14" fill="#fff6ed" stroke="#db8129" stroke-width="3" />')
    # Icon for Callout 1: warning / alert icon (56px, orange stroke)
    svg.append('  <g transform="translate(320, 852)">')
    svg.append('    <polygon points="28,8 52,48 4,48" fill="#ffffff" stroke="#db8129" stroke-width="4" stroke-linejoin="round" />')
    svg.append('    <line x1="28" y1="24" x2="28" y2="34" stroke="#db8129" stroke-width="4" stroke-linecap="round" />')
    svg.append('    <circle cx="28" cy="42" r="2.5" fill="#db8129" />')
    svg.append('  </g>')
    # Text for Callout 1
    svg.append('  <text x="395" y="784" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="395" dy="0" font-weight="bold">queue full: the server drops the final ACK</tspan>')
    svg.append('    <tspan x="395" dy="35">or ignores the SYN; the client believes it is</tspan>')
    svg.append('    <tspan x="395" dy="35">connected and retransmits; latency spikes</tspan>')
    svg.append('    <tspan x="395" dy="35">of 1, 3 and 7 seconds; nstat counters</tspan>')
    svg.append('    <tspan x="395" dy="35" font-family="monospace">ListenOverflows</tspan><tspan font-family="sans-serif"> and </tspan><tspan font-family="monospace">ListenDrops</tspan><tspan font-family="sans-serif"> climb</tspan>')
    svg.append('  </text>')

    # Right Fix List (x: 1100..1550, width = 450)
    # Fix 1: raise somaxconn to 4096 or more (y: 150..300)
    svg.append('  <rect x="1100" y="150" width="450" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1120, 197)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <line x1="12" y1="28" x2="44" y2="28" stroke="#207448" stroke-width="4" stroke-linecap="round" />')
    svg.append('    <circle cx="36" cy="28" r="7" fill="#207448" />')
    svg.append('  </g>')
    svg.append('  <text x="1195" y="215" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('    <tspan x="1195" dy="0" font-weight="bold">raise somaxconn</tspan>')
    svg.append('    <tspan x="1195" dy="36">to 4096 or more</tspan>')
    svg.append('  </text>')

    # Fix 2: set the application backlog too, such as nginx listen ... backlog= (y: 330..480)
    svg.append('  <rect x="1100" y="330" width="450" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1120, 377)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="28" cy="28" r="16" fill="none" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="28" cy="28" r="6" fill="#207448" />')
    svg.append('  </g>')
    svg.append('  <text x="1195" y="385" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1195" dy="0" font-weight="bold">set the application backlog</tspan>')
    svg.append('    <tspan x="1195" dy="32">too, such as </tspan><tspan font-family="monospace">nginx listen</tspan>')
    svg.append('    <tspan x="1195" dy="32" font-family="monospace">... backlog=</tspan>')
    svg.append('  </text>')

    # Fix 3: Go's net.Listen uses somaxconn (y: 510..660)
    svg.append('  <rect x="1100" y="510" width="450" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1120, 557)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <path d="M 16 38 L 28 18 L 40 38" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />')
    svg.append('  </g>')
    svg.append('  <text x="1195" y="575" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('    <tspan x="1195" dy="0" font-weight="bold">Go&apos;s net.Listen</tspan>')
    svg.append('    <tspan x="1195" dy="36">uses somaxconn</tspan>')
    svg.append('  </text>')

    # Fix 4: fix any slow accept() loop, because that loop is what fills the queue (y: 690..840)
    svg.append('  <rect x="1100" y="690" width="450" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1120, 737)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="28" cy="28" r="16" fill="none" stroke="#207448" stroke-width="3" stroke-dasharray="10 4" />')
    svg.append('  </g>')
    svg.append('  <text x="1195" y="745" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1195" dy="0" font-weight="bold">fix any slow accept() loop,</tspan>')
    svg.append('    <tspan x="1195" dy="32">because that loop is what</tspan>')
    svg.append('    <tspan x="1195" dy="32">fills the queue</tspan>')
    svg.append('  </text>')

    # Fix 5: ss -ltn shows queue length in Recv-Q (y: 870..1020)
    svg.append('  <rect x="1100" y="870" width="450" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1120, 917)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <polyline points="16,20 26,28 16,36" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')
    svg.append('    <line x1="30" y1="36" x2="40" y2="36" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    svg.append('  </g>')
    svg.append('  <text x="1195" y="935" font-family="sans-serif" font-size="25" fill="#303a36">')
    svg.append('    <tspan x="1195" dy="0" font-family="monospace" font-weight="bold">ss -ltn</tspan><tspan font-family="sans-serif"> shows queue length</tspan>')
    svg.append('    <tspan x="1195" dy="36">in </tspan><tspan font-family="monospace">Recv-Q</tspan>')
    svg.append('  </text>')

    # Bottom bar (y: 1080..1140)
    svg.append('  <rect x="50" y="1080" width="1500" height="60" rx="10" fill="#207448" />')
    svg.append('  <text x="800" y="1118" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">Check ListenOverflows before you change any setting</text>')

    svg.append('</svg>')
    return "\n".join(svg)

content = build_svg()
pathlib.Path("test_full_candidate.svg").write_text(content)
print("Saved test_full_candidate.svg")
