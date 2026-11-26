import re

# Let's adjust generate_perfect_svg.py with exact padding calculations
with open("generate_perfect_svg.py", "r") as f:
    code = f.read()

# Let's write an updated generator that passes all audits and all padding assertions
generator_script = '''
import re
import pathlib
import xml.etree.ElementTree as ET

def build_svg():
    W = 1600
    H = 1180

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>The two queues behind listen(): where a busy server drops connections</title>')
    svg.append('  <desc>Visual explanation of the SYN queue and Accept queue behind listen(), connection flow, failure callouts, and tuning fixes.</desc>')

    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">')
    svg.append('      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect x="0" y="0" width="{W}" height="{H}" fill="#f5f8f5" />')

    # Title: 48px bold
    svg.append('  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">The two queues behind listen():</tspan>')
    svg.append('    <tspan x="800" dy="54">where a busy server drops connections</tspan>')
    svg.append('  </text>')

    # Left: Client Box (x: 50..150, width: 100, y: 140..730, height: 590)
    svg.append('  <rect x="50" y="140" width="100" height="590" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Client icon inside box
    svg.append('  <g transform="translate(72, 400)">')
    svg.append('    <rect x="0" y="0" width="56" height="40" rx="4" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <line x1="8" y1="12" x2="48" y2="12" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
    svg.append('    <line x1="8" y1="22" x2="36" y2="22" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />')
    svg.append('    <line x1="28" y1="40" x2="28" y2="50" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />')
    svg.append('    <line x1="12" y1="50" x2="44" y2="50" stroke="#207448" stroke-width="3.5" stroke-linecap="round" />')
    svg.append('  </g>')

    # Handshake Arrows between Client and Server
    # Arrow 1: SYN (Client -> SYN queue)
    svg.append('  <line x1="150" y1="175" x2="300" y2="175" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('  <text x="225" y="165" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">SYN</text>')

    # Arrow 2: SYN-ACK (SYN queue -> Client)
    svg.append('  <line x1="300" y1="220" x2="150" y2="220" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('  <text x="225" y="210" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">SYN-ACK</text>')

    # Arrow 3: ACK (Client -> Accept queue)
    svg.append('  <line x1="150" y1="645" x2="300" y2="645" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')
    svg.append('  <text x="225" y="635" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">ACK</text>')

    # Server container border (subtle container background)
    svg.append('  <rect x="285" y="130" width="750" height="940" rx="18" fill="none" stroke="#207448" stroke-width="1.5" stroke-dasharray="8 6" opacity="0.35" />')

    # Tier 1: SYN queue box (x: 300..1020, width: 720, y: 140..245, height: 105)
    svg.append('  <rect x="300" y="140" width="720" height="105" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # SYN queue icon (56px)
    svg.append('  <g transform="translate(320, 165)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    svg.append('    <line x1="18" y1="12" x2="18" y2="44" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    svg.append('    <line x1="36" y1="12" x2="36" y2="44" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    svg.append('    <circle cx="9" cy="28" r="4" fill="#207448" />')
    svg.append('    <circle cx="27" cy="28" r="4" fill="#207448" />')
    svg.append('  </g>')
    # SYN queue text
    svg.append('  <text x="395" y="180" font-family="sans-serif" font-size="28" fill="#303a36">')
    svg.append('    <tspan x="395" dy="0" font-weight="bold">SYN queue: half-open connections,</tspan>')
    svg.append('    <tspan x="395" dy="38" font-family="monospace" font-size="24">size set by tcp_max_syn_backlog</tspan>')
    svg.append('  </text>')

    # Tier 2: Callout 2 on SYN queue (x: 300..1020, width: 720, y: 285..520, height: 235)
    # Gap from SYN queue (245) = 40px >= 40px
    svg.append('  <rect x="300" y="285" width="720" height="235" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Callout 2 icon: ticket / badge (56px)
    svg.append('  <g transform="translate(320, 375)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <path d="M 12 28 Q 28 14 44 28 Q 28 48 12 28 Z" fill="none" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="28" cy="28" r="5" fill="#207448" />')
    svg.append('  </g>')
    # Callout 2 text (8 lines, all width <= 533px, text_x = 395, padding >= 90px)
    svg.append('  <text x="395" y="324" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="395" dy="0" font-weight="bold">SYN flood or sudden burst fills it;</tspan>')
    svg.append('    <tspan x="395" dy="24">fix with </tspan><tspan font-family="monospace">net.ipv4.tcp_syncookies=1:</tspan>')
    svg.append('    <tspan x="395" dy="24">the kernel encodes the connection</tspan>')
    svg.append('    <tspan x="395" dy="24">state in the SYN-ACK sequence number,</tspan>')
    svg.append('    <tspan x="395" dy="24">so no queue entry is needed, at the</tspan>')
    svg.append('    <tspan x="395" dy="24">cost of losing some options (a clinic</tspan>')
    svg.append('    <tspan x="395" dy="24">that hands each visitor a ticket</tspan>')
    svg.append('    <tspan x="395" dy="24">instead of keeping a waiting list)</tspan>')
    svg.append('  </text>')

    # Tier 3: Accept queue (x: 300..720, width: 420) and application accept() loop (x: 760..1020, width: 260)
    # y: 560..730, height: 170. Gap from Callout 2 (520) = 40px >= 40px
    svg.append('  <rect x="300" y="560" width="420" height="170" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # Accept queue icon (56px)
    svg.append('  <g transform="translate(315, 617)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    svg.append('    <path d="M 14 28 L 24 38 L 42 18" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />')
    svg.append('  </g>')
    # Accept queue text
    svg.append('  <text x="385" y="595" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('    <tspan x="385" dy="0" font-weight="bold">Accept queue:</tspan>')
    svg.append('    <tspan x="385" dy="30" font-size="24">completed handshakes</tspan>')
    svg.append('    <tspan x="385" dy="27" font-size="24">waiting for accept(),</tspan>')
    svg.append('    <tspan x="385" dy="29" font-family="monospace" font-size="24">size min(backlog,</tspan>')
    svg.append('    <tspan x="385" dy="27" font-family="monospace" font-size="24">net.core.somaxconn)</tspan>')
    svg.append('  </text>')

    # Arrow 4: Accept queue -> application accept() loop (gap: 720 to 760, width 40)
    svg.append('  <line x1="720" y1="645" x2="760" y2="645" stroke="#207448" stroke-width="3" marker-end="url(#arrow)" />')

    # application accept() loop (x: 760..1020, width: 260, y: 560..730, height: 170)
    svg.append('  <rect x="760" y="560" width="260" height="170" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Loop / gear icon
    svg.append('  <g transform="translate(862, 576)">')
    svg.append('    <circle cx="28" cy="28" r="20" fill="none" stroke="#207448" stroke-width="3" stroke-dasharray="14 5" />')
    svg.append('    <circle cx="28" cy="28" r="9" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('  </g>')
    # application accept() loop text
    svg.append('  <text x="890" y="670" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="890" dy="0">application</tspan>')
    svg.append('    <tspan x="890" dy="32">accept() loop</tspan>')
    svg.append('  </text>')

    # Tier 4: Callout 1 on Accept queue (orange) (x: 300..1020, width: 720, y: 770..1060, height: 290)
    # Gap from Accept queue (730) = 40px >= 40px
    svg.append('  <rect x="300" y="770" width="720" height="290" rx="14" fill="#fff6ed" stroke="#db8129" stroke-width="3" />')
    # Warning triangle icon (56px, orange)
    svg.append('  <g transform="translate(320, 887)">')
    svg.append('    <polygon points="28,8 52,48 4,48" fill="#ffffff" stroke="#db8129" stroke-width="4" stroke-linejoin="round" />')
    svg.append('    <line x1="28" y1="24" x2="28" y2="34" stroke="#db8129" stroke-width="4" stroke-linecap="round" />')
    svg.append('    <circle cx="28" cy="42" r="2.5" fill="#db8129" />')
    svg.append('  </g>')
    # Callout 1 text (6 lines, balanced, all <= 546px, padding >= 84px)
    svg.append('  <text x="395" y="825" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="395" dy="0" font-weight="bold">queue full: the server drops the</tspan>')
    svg.append('    <tspan x="395" dy="36">final ACK or ignores the SYN; the</tspan>')
    svg.append('    <tspan x="395" dy="36">client believes it is connected and</tspan>')
    svg.append('    <tspan x="395" dy="36">retransmits; latency spikes of 1, 3</tspan>')
    svg.append('    <tspan x="395" dy="36">and 7 seconds; nstat counters</tspan>')
    svg.append('    <tspan x="395" dy="36" font-family="monospace">ListenOverflows</tspan><tspan font-family="sans-serif"> and </tspan><tspan font-family="monospace">ListenDrops</tspan><tspan font-family="sans-serif"> climb</tspan>')
    svg.append('  </text>')

    # Right Fix List (x: 1080..1550, width: 470)
    # Gap from Server container (1035) = 45px >= 40px
    # 5 cards with height 144, gaps 50px

    # Card 1: raise somaxconn to 4096 or more (y: 140..284)
    svg.append('  <rect x="1080" y="140" width="470" height="144" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1105, 184)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <line x1="12" y1="28" x2="44" y2="28" stroke="#207448" stroke-width="4" stroke-linecap="round" />')
    svg.append('    <circle cx="36" cy="28" r="7" fill="#207448" />')
    svg.append('  </g>')
    svg.append('  <text x="1180" y="202" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('    <tspan x="1180" dy="0" font-weight="bold">raise somaxconn</tspan>')
    svg.append('    <tspan x="1180" dy="36">to 4096 or more</tspan>')
    svg.append('  </text>')

    # Card 2: set the application backlog too, such as nginx listen ... backlog= (y: 334..478, gap = 50px)
    svg.append('  <rect x="1080" y="334" width="470" height="144" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1105, 378)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="28" cy="28" r="16" fill="none" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="28" cy="28" r="6" fill="#207448" />')
    svg.append('  </g>')
    svg.append('  <text x="1180" y="375" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1180" dy="0" font-weight="bold">set the application</tspan>')
    svg.append('    <tspan x="1180" dy="29">backlog too, such as</tspan>')
    svg.append('    <tspan x="1180" dy="29" font-family="monospace">nginx listen ...</tspan>')
    svg.append('    <tspan x="1180" dy="28" font-family="monospace">backlog=</tspan>')
    svg.append('  </text>')

    # Card 3: Go's net.Listen uses somaxconn (y: 528..672, gap = 50px)
    svg.append('  <rect x="1080" y="528" width="470" height="144" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1105, 572)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <path d="M 16 38 L 28 18 L 40 38" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />')
    svg.append('  </g>')
    svg.append('  <text x="1180" y="590" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('    <tspan x="1180" dy="0" font-weight="bold">Go&apos;s net.Listen</tspan>')
    svg.append('    <tspan x="1180" dy="36">uses somaxconn</tspan>')
    svg.append('  </text>')

    # Card 4: fix any slow accept() loop, because that loop is what fills the queue (y: 722..866, gap = 50px)
    svg.append('  <rect x="1080" y="722" width="470" height="144" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1105, 766)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <circle cx="28" cy="28" r="16" fill="none" stroke="#207448" stroke-width="3" stroke-dasharray="10 4" />')
    svg.append('  </g>')
    svg.append('  <text x="1180" y="763" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1180" dy="0" font-weight="bold">fix any slow</tspan>')
    svg.append('    <tspan x="1180" dy="29">accept() loop, because</tspan>')
    svg.append('    <tspan x="1180" dy="29">that loop is what</tspan>')
    svg.append('    <tspan x="1180" dy="29">fills the queue</tspan>')
    svg.append('  </text>')

    # Card 5: ss -ltn shows queue length in Recv-Q (y: 916..1060, gap = 50px)
    svg.append('  <rect x="1080" y="916" width="470" height="144" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <g transform="translate(1105, 960)">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="8" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    svg.append('    <polyline points="16,20 26,28 16,36" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />')
    svg.append('    <line x1="30" y1="36" x2="40" y2="36" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    svg.append('  </g>')
    svg.append('  <text x="1180" y="978" font-family="sans-serif" font-size="25" fill="#303a36">')
    svg.append('    <tspan x="1180" dy="0" font-family="monospace" font-weight="bold">ss -ltn</tspan><tspan font-family="sans-serif"> shows</tspan>')
    svg.append('    <tspan x="1180" dy="36">queue length in </tspan><tspan font-family="monospace">Recv-Q</tspan>')
    svg.append('  </text>')

    # Bottom bar (y: 1100..1160, height: 60)
    # Gap from 1060 is 40px >= 40px
    svg.append('  <rect x="50" y="1100" width="1500" height="60" rx="10" fill="#207448" />')
    svg.append('  <text x="800" y="1139" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Check ListenOverflows before you change any setting</text>')

    svg.append('</svg>')
    return "\n".join(svg)

content = build_svg()
pathlib.Path("perfect_candidate.svg").write_text(content)
print("Updated perfect_candidate.svg")
'''

with open("generate_perfect_svg.py", "w") as f:
    f.write(generator_script)

