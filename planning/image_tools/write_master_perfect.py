#!/usr/bin/env python3

def generate_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Reading the sample trace line by line as a conversation</title>
  <desc>Visual sequence diagram and ladder trace of a network conversation between duplex.example.com client and mikado.example.com server showing ARP resolution, TCP three-way handshake, HTTP request and response with ACKs, packet filter summary, and flag legend.</desc>

  <defs>
    <!-- Normal green arrow marker (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <!-- Orange arrow marker for the single most important arrow (SYN) (18px) -->
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- ==================== TITLE (2 lines with generous margins) ==================== -->
  <text x="800" y="76" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36"><tspan x="800" dy="0">Reading the sample trace </tspan><tspan x="800" dy="54">line by line as a conversation</tspan></text>

  <!-- ==================== HOST NODES (SWIMLANES) ==================== -->

  <!-- Host 1 (Client): duplex.example.com (client) -->
  <g id="host-client">
    <rect x="380" y="170" width="520" height="100" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Outline icon: Workstation / Client terminal (56px) -->
    <g transform="translate(405, 192)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="32" rx="4" />
      <line x1="2" y1="46" x2="54" y2="46" />
      <polyline points="14,18 22,23 14,28" />
      <line x1="26" y1="28" x2="40" y2="28" />
    </g>
    <text x="485" y="210" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36"><tspan x="485" dy="0">duplex.example.com </tspan><tspan x="485" dy="36">(client)</tspan></text>
  </g>

  <!-- Host 2 (Server): mikado.example.com (server) -->
  <g id="host-server">
    <rect x="1040" y="170" width="520" height="100" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Outline icon: Rack Server chassis (56px) -->
    <g transform="translate(1065, 192)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="44" rx="4" />
      <line x1="6" y1="20" x2="50" y2="20" />
      <line x1="6" y1="34" x2="50" y2="34" />
      <circle cx="16" cy="13" r="2" fill="#207448" />
      <circle cx="24" cy="13" r="2" fill="#207448" />
      <circle cx="16" cy="27" r="2" fill="#207448" />
      <circle cx="24" cy="27" r="2" fill="#207448" />
      <circle cx="16" cy="41" r="2" fill="#207448" />
      <circle cx="24" cy="41" r="2" fill="#207448" />
      <line x1="34" y1="13" x2="44" y2="13" />
      <line x1="34" y1="27" x2="44" y2="27" />
      <line x1="34" y1="41" x2="44" y2="41" />
    </g>
    <text x="1145" y="210" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36"><tspan x="1145" dy="0">mikado.example.com </tspan><tspan x="1145" dy="36">(server)</tspan></text>
  </g>

  <!-- Vertical Lifelines for swimlanes -->
  <!-- Client lifeline at x=640 -->
  <line x1="640" y1="270" x2="640" y2="780" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" />
  <!-- Server lifeline at x=1440 -->
  <line x1="1440" y1="270" x2="1440" y2="780" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" />

  <!-- ==================== LEFT BRACKETS ==================== -->

  <!-- Bracket 1: lines 1-2 (y=258..418, h=160) -->
  <g id="bracket-group-1">
    <rect x="40" y="258" width="370" height="160" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="225" y="294" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="225" dy="0">lines 1-2: finding the </tspan><tspan x="225" dy="25">link address because </tspan><tspan x="225" dy="25">the client needs the </tspan><tspan x="225" dy="25">server&apos;s MAC before it </tspan><tspan x="225" dy="25">can send a frame</tspan></text>
    <!-- Visual bracket grouping lines 1 & 2 -->
    <path d="M 410 310 H 425 V 337.5 H 440 H 425 V 365 H 410" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Bracket 2: lines 3-5 (y=458..558, h=100) -->
  <g id="bracket-group-2">
    <rect x="40" y="458" width="370" height="100" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="225" y="500" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="225" dy="0">lines 3-5: </tspan><tspan x="225" dy="28">three-way handshake</tspan></text>
    <!-- Visual bracket grouping lines 3, 4, 5 -->
    <path d="M 410 420 H 425 V 475 H 440 H 425 V 530 H 410" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Bracket 3: lines 6-9 (y=598..760, h=162) -->
  <g id="bracket-group-3">
    <rect x="40" y="598" width="370" height="162" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="225" y="687" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">lines 6-9: data</text>
    <!-- Visual bracket grouping lines 6, 7, 8, 9 -->
    <path d="M 410 585 H 425 V 667.5 H 440 H 425 V 750 H 410" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- ==================== NUMBERED LADDER (LINES 1 TO 9) ==================== -->

  <!-- Line 1: client to server -->
  <g id="ladder-line-1">
    <circle cx="490" cy="310" r="24" fill="#207448" />
    <text x="490" y="318" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Arrow: client (640) to server (1440) -->
    <line x1="640" y1="310" x2="1440" y2="310" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="298" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">arp who-has mikado tell duplex</text>
  </g>

  <!-- Line 2: server to client -->
  <g id="ladder-line-2">
    <circle cx="490" cy="365" r="24" fill="#207448" />
    <text x="490" y="373" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Arrow: server (1440) to client (640) -->
    <line x1="1440" y1="365" x2="640" y2="365" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="353" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">arp reply mikado is-at 0:2:2d:b:ee:4e</text>
  </g>

  <!-- Line 3: client to server SYN (Single most important item: highlighted in orange) -->
  <g id="ladder-line-3">
    <circle cx="490" cy="420" r="24" fill="#db8129" />
    <text x="490" y="428" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- Arrow: client (640) to server (1440) in orange -->
    <line x1="640" y1="420" x2="1440" y2="420" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />
    <!-- Monospace packet label -->
    <text x="1040" y="408" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S 3200063165 win 5840 mss 1460 sackOK (DF)</text>
  </g>

  <!-- Line 4: server to client SYN-ACK -->
  <g id="ladder-line-4">
    <circle cx="490" cy="475" r="24" fill="#207448" />
    <text x="490" y="483" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Arrow: server (1440) to client (640) -->
    <line x1="1440" y1="475" x2="640" y2="475" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="463" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S ack 3200063166 win 5792</text>
  </g>

  <!-- Line 5: client to server ACK -->
  <g id="ladder-line-5">
    <circle cx="490" cy="530" r="24" fill="#207448" />
    <text x="490" y="538" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Arrow: client (640) to server (1440) -->
    <line x1="640" y1="530" x2="1440" y2="530" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="518" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 1</text>
  </g>

  <!-- Line 6: client to server request -->
  <g id="ladder-line-6">
    <circle cx="490" cy="585" r="24" fill="#207448" />
    <text x="490" y="593" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">6</text>
    <!-- Arrow: client (640) to server (1440) -->
    <line x1="640" y1="585" x2="1440" y2="585" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="573" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">P 1:427(426)</text>
  </g>

  <!-- Line 7: server to client ACK -->
  <g id="ladder-line-7">
    <circle cx="490" cy="640" r="24" fill="#207448" />
    <text x="490" y="648" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">7</text>
    <!-- Arrow: server (1440) to client (640) -->
    <line x1="1440" y1="640" x2="640" y2="640" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="628" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 427</text>
  </g>

  <!-- Line 8: server to client response -->
  <g id="ladder-line-8">
    <circle cx="490" cy="695" r="24" fill="#207448" />
    <text x="490" y="703" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">8</text>
    <!-- Arrow: server (1440) to client (640) -->
    <line x1="1440" y1="695" x2="640" y2="695" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="683" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">P 1:773(772)</text>
  </g>

  <!-- Line 9: client to server ACK -->
  <g id="ladder-line-9">
    <circle cx="490" cy="750" r="24" fill="#207448" />
    <text x="490" y="758" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">9</text>
    <!-- Arrow: client (640) to server (1440) -->
    <line x1="640" y1="750" x2="1440" y2="750" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="738" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 773</text>
  </g>

  <!-- ==================== FLAG LEGEND ==================== -->
  <g id="panel-legend">
    <rect x="40" y="820" width="1520" height="60" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="858" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S SYN, S. SYN-ACK, . ACK, P. PSH-ACK, F. FIN-ACK, R or R. RST</text>
  </g>

  <!-- ==================== FOOTER ==================== -->
  <g id="panel-footer">
    <rect x="40" y="920" width="1520" height="60" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="958" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">summary: 9 packets received by filter, 0 packets dropped by kernel</text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="panel-bottom-bar">
    <rect x="40" y="1025" width="1520" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <text x="800" y="1075" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448"><tspan x="800" dy="0">Read the flags in order; a SYN with no reply stops the story at the first line, </tspan><tspan x="800" dy="36">and the next question is who stayed silent</tspan></text>
  </g>
</svg>'''

if __name__ == "__main__":
    content = generate_svg()
    with open("master_perfect.svg", "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote master_perfect.svg")
