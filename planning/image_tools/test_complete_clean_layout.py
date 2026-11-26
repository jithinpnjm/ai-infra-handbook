#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

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

  <!-- ==================== TITLE (2 lines for generous outside margin) ==================== -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36"><tspan x="800" dy="0">Reading the sample trace </tspan><tspan x="800" dy="54">line by line as a conversation</tspan></text>

  <!-- ==================== HOST NODES (SWIMLANES) ==================== -->

  <!-- Host 1 (Client): duplex.example.com (client) -->
  <g id="host-client">
    <rect x="380" y="140" width="520" height="100" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Outline icon: Workstation / Client terminal (56px) -->
    <g transform="translate(405, 162)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="32" rx="4" />
      <line x1="2" y1="46" x2="54" y2="46" />
      <polyline points="14,18 22,23 14,28" />
      <line x1="26" y1="28" x2="40" y2="28" />
    </g>
    <text x="485" y="180" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36"><tspan x="485" dy="0">duplex.example.com </tspan><tspan x="485" dy="36">(client)</tspan></text>
  </g>

  <!-- Host 2 (Server): mikado.example.com (server) -->
  <g id="host-server">
    <rect x="1040" y="140" width="520" height="100" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Outline icon: Rack Server chassis (56px) -->
    <g transform="translate(1065, 162)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
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
    <text x="1145" y="180" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36"><tspan x="1145" dy="0">mikado.example.com </tspan><tspan x="1145" dy="36">(server)</tspan></text>
  </g>

  <!-- Vertical Lifelines for swimlanes -->
  <!-- Client lifeline at x=640 -->
  <line x1="640" y1="240" x2="640" y2="785" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" />
  <!-- Server lifeline at x=1440 -->
  <line x1="1440" y1="240" x2="1440" y2="785" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" />

  <!-- ==================== LEFT BRACKETS ==================== -->

  <!-- Bracket 1: lines 1-2 (y=250..390, h=140) -->
  <g id="bracket-group-1">
    <rect x="40" y="250" width="370" height="140" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="225" y="278" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="225" dy="0">lines 1-2: finding the link </tspan><tspan x="225" dy="26">address because the client </tspan><tspan x="225" dy="26">needs the server&apos;s MAC </tspan><tspan x="225" dy="26">before it can send a frame</tspan></text>
    <!-- Visual bracket grouping lines 1 & 2 -->
    <path d="M 410 290 H 425 V 319 H 438 H 425 V 348 H 410" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Bracket 2: lines 3-5 (y=430..540, h=110) -->
  <g id="bracket-group-2">
    <rect x="40" y="430" width="370" height="110" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="225" y="476" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="225" dy="0">lines 3-5: </tspan><tspan x="225" dy="32">three-way handshake</tspan></text>
    <!-- Visual bracket grouping lines 3, 4, 5 -->
    <path d="M 410 406 H 425 V 464 H 438 H 425 V 522 H 410" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Bracket 3: lines 6-9 (y=580..755, h=175) -->
  <g id="bracket-group-3">
    <rect x="40" y="580" width="370" height="175" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="225" y="675" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">lines 6-9: data</text>
    <!-- Visual bracket grouping lines 6, 7, 8, 9 -->
    <path d="M 410 580 H 425 V 667 H 438 H 425 V 754 H 410" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- ==================== NUMBERED LADDER (LINES 1 TO 9) ==================== -->

  <!-- Line 1: client to server -->
  <g id="ladder-line-1">
    <circle cx="490" cy="290" r="24" fill="#207448" />
    <text x="490" y="298" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Arrow: client (640) to server (1440) -->
    <line x1="640" y1="290" x2="1440" y2="290" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="276" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">arp who-has mikado tell duplex</text>
  </g>

  <!-- Line 2: server to client -->
  <g id="ladder-line-2">
    <circle cx="490" cy="348" r="24" fill="#207448" />
    <text x="490" y="356" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Arrow: server (1440) to client (640) -->
    <line x1="1440" y1="348" x2="640" y2="348" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="334" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">arp reply mikado is-at 0:2:2d:b:ee:4e</text>
  </g>

  <!-- Line 3: client to server SYN (Single most important item: highlighted in orange) -->
  <g id="ladder-line-3">
    <circle cx="490" cy="406" r="24" fill="#db8129" />
    <text x="490" y="414" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- Arrow: client (640) to server (1440) in orange -->
    <line x1="640" y1="406" x2="1440" y2="406" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />
    <!-- Monospace packet label -->
    <text x="1040" y="392" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S 3200063165 win 5840 mss 1460 sackOK (DF)</text>
  </g>

  <!-- Line 4: server to client SYN-ACK -->
  <g id="ladder-line-4">
    <circle cx="490" cy="464" r="24" fill="#207448" />
    <text x="490" y="472" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Arrow: server (1440) to client (640) -->
    <line x1="1440" y1="464" x2="640" y2="464" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="450" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S ack 3200063166 win 5792</text>
  </g>

  <!-- Line 5: client to server ACK -->
  <g id="ladder-line-5">
    <circle cx="490" cy="522" r="24" fill="#207448" />
    <text x="490" y="530" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Arrow: client (640) to server (1440) -->
    <line x1="640" y1="522" x2="1440" y2="522" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="508" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 1</text>
  </g>

  <!-- Line 6: client to server request -->
  <g id="ladder-line-6">
    <circle cx="490" cy="580" r="24" fill="#207448" />
    <text x="490" y="588" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">6</text>
    <!-- Arrow: client (640) to server (1440) -->
    <line x1="640" y1="580" x2="1440" y2="580" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="566" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">P 1:427(426)</text>
  </g>

  <!-- Line 7: server to client ACK -->
  <g id="ladder-line-7">
    <circle cx="490" cy="638" r="24" fill="#207448" />
    <text x="490" y="646" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">7</text>
    <!-- Arrow: server (1440) to client (640) -->
    <line x1="1440" y1="638" x2="640" y2="638" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="624" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 427</text>
  </g>

  <!-- Line 8: server to client response -->
  <g id="ladder-line-8">
    <circle cx="490" cy="696" r="24" fill="#207448" />
    <text x="490" y="704" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">8</text>
    <!-- Arrow: server (1440) to client (640) -->
    <line x1="1440" y1="696" x2="640" y2="696" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="682" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">P 1:773(772)</text>
  </g>

  <!-- Line 9: client to server ACK -->
  <g id="ladder-line-9">
    <circle cx="490" cy="754" r="24" fill="#207448" />
    <text x="490" y="762" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">9</text>
    <!-- Arrow: client (640) to server (1440) -->
    <line x1="640" y1="754" x2="1440" y2="754" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1040" y="740" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 773</text>
  </g>

  <!-- ==================== FLAG LEGEND ==================== -->
  <g id="panel-legend">
    <rect x="40" y="825" width="1520" height="60" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="863" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S SYN, S. SYN-ACK, . ACK, P. PSH-ACK, F. FIN-ACK, R or R. RST</text>
  </g>

  <!-- ==================== FOOTER ==================== -->
  <g id="panel-footer">
    <rect x="40" y="930" width="1520" height="60" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="968" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">summary: 9 packets received by filter, 0 packets dropped by kernel</text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="panel-bottom-bar">
    <rect x="40" y="1035" width="1520" height="115" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <text x="800" y="1083" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448"><tspan x="800" dy="0">Read the flags in order; a SYN with no reply stops the story at the first line, </tspan><tspan x="800" dy="36">and the next question is who stayed silent</tspan></text>
  </g>
</svg>'''

if __name__ == "__main__":
    content = generate_svg()
    with open("candidate_read_conv_clean.svg", "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote candidate_read_conv_clean.svg")
