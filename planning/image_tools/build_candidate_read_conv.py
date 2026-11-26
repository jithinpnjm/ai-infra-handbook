#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def create_svg():
    # Canvas: 1600 x 1200
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
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

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Reading the sample trace line by line as a conversation</text>

  <!-- ==================== HOST NODES (SWIMLANES) ==================== -->

  <!-- Host 1 (Client): duplex.example.com (client) -->
  <g id="host-client">
    <rect x="470" y="85" width="450" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Outline icon: Workstation / Client terminal (56px) -->
    <g transform="translate(490, 124)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="32" rx="4" />
      <line x1="2" y1="46" x2="54" y2="46" />
      <polyline points="14,18 22,23 14,28" />
      <line x1="26" y1="28" x2="40" y2="28" />
    </g>
    <text x="735" y="142" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="735" dy="0">duplex.example.com </tspan>
      <tspan x="735" dy="36">(client)</tspan>
    </text>
  </g>

  <!-- Host 2 (Server): mikado.example.com (server) -->
  <g id="host-server">
    <rect x="1110" y="85" width="450" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Outline icon: Rack Server chassis (56px) -->
    <g transform="translate(1130, 124)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
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
    <text x="1375" y="142" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
      <tspan x="1375" dy="0">mikado.example.com </tspan>
      <tspan x="1375" dy="36">(server)</tspan>
    </text>
  </g>

  <!-- Vertical Lifelines for swimlanes -->
  <!-- Client lifeline at x=695 -->
  <line x1="695" y1="220" x2="695" y2="825" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" />
  <!-- Server lifeline at x=1335 -->
  <line x1="1335" y1="220" x2="1335" y2="825" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" />

  <!-- ==================== LEFT BRACKETS ==================== -->

  <!-- Bracket 1: lines 1-2 (y=245..370, h=125) -->
  <g id="bracket-group-1">
    <rect x="40" y="245" width="410" height="125" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="245" y="271" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="245" dy="0">lines 1-2: finding the link</tspan>
      <tspan x="245" dy="26">address because the client</tspan>
      <tspan x="245" dy="26">needs the server&apos;s MAC</tspan>
      <tspan x="245" dy="26">before it can send a frame</tspan>
    </text>
    <!-- Visual bracket grouping lines 1 & 2 -->
    <path d="M 450 270 H 465 V 302 H 478 H 465 V 335 H 450" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Bracket 2: lines 3-5 (y=410..520, h=110) -->
  <g id="bracket-group-2">
    <rect x="40" y="410" width="410" height="110" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="245" y="456" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="245" dy="0">lines 3-5: </tspan>
      <tspan x="245" dy="32">three-way handshake</tspan>
    </text>
    <!-- Visual bracket grouping lines 3, 4, 5 -->
    <path d="M 450 400 H 465 V 465 H 478 H 465 V 530 H 450" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Bracket 3: lines 6-9 (y=620..765, h=145) -->
  <g id="bracket-group-3">
    <rect x="40" y="620" width="410" height="145" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="245" y="700" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">lines 6-9: data</text>
    <!-- Visual bracket grouping lines 6, 7, 8, 9 -->
    <path d="M 450 595 H 465 V 692 H 478 H 465 V 790 H 450" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- ==================== NUMBERED LADDER (LINES 1 TO 9) ==================== -->

  <!-- Line 1: client to server -->
  <g id="ladder-line-1">
    <circle cx="515" cy="270" r="24" fill="#207448" />
    <text x="515" y="278" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Arrow: client (695) to server (1335) -->
    <line x1="695" y1="270" x2="1335" y2="270" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1015" y="256" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">arp who-has mikado tell duplex</text>
  </g>

  <!-- Line 2: server to client -->
  <g id="ladder-line-2">
    <circle cx="515" cy="335" r="24" fill="#207448" />
    <text x="515" y="343" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Arrow: server (1335) to client (695) -->
    <line x1="1335" y1="335" x2="695" y2="335" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1015" y="321" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">arp reply mikado is-at 0:2:2d:b:ee:4e</text>
  </g>

  <!-- Line 3: client to server SYN (Single most important item: highlighted in orange) -->
  <g id="ladder-line-3">
    <circle cx="515" cy="400" r="24" fill="#db8129" />
    <text x="515" y="408" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- Arrow: client (695) to server (1335) in orange -->
    <line x1="695" y1="400" x2="1335" y2="400" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />
    <!-- Monospace packet label -->
    <text x="1015" y="386" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S 3200063165 win 5840 mss 1460 sackOK (DF)</text>
  </g>

  <!-- Line 4: server to client SYN-ACK -->
  <g id="ladder-line-4">
    <circle cx="515" cy="465" r="24" fill="#207448" />
    <text x="515" y="473" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Arrow: server (1335) to client (695) -->
    <line x1="1335" y1="465" x2="695" y2="465" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1015" y="451" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S ack 3200063166 win 5792</text>
  </g>

  <!-- Line 5: client to server ACK -->
  <g id="ladder-line-5">
    <circle cx="515" cy="530" r="24" fill="#207448" />
    <text x="515" y="538" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Arrow: client (695) to server (1335) -->
    <line x1="695" y1="530" x2="1335" y2="530" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1015" y="516" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 1</text>
  </g>

  <!-- Line 6: client to server request -->
  <g id="ladder-line-6">
    <circle cx="515" cy="595" r="24" fill="#207448" />
    <text x="515" y="603" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">6</text>
    <!-- Arrow: client (695) to server (1335) -->
    <line x1="695" y1="595" x2="1335" y2="595" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1015" y="581" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">P 1:427(426)</text>
  </g>

  <!-- Line 7: server to client ACK -->
  <g id="ladder-line-7">
    <circle cx="515" cy="660" r="24" fill="#207448" />
    <text x="515" y="668" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">7</text>
    <!-- Arrow: server (1335) to client (695) -->
    <line x1="1335" y1="660" x2="695" y2="660" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1015" y="646" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 427</text>
  </g>

  <!-- Line 8: server to client response -->
  <g id="ladder-line-8">
    <circle cx="515" cy="725" r="24" fill="#207448" />
    <text x="515" y="733" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">8</text>
    <!-- Arrow: server (1335) to client (695) -->
    <line x1="1335" y1="725" x2="695" y2="725" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1015" y="711" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">P 1:773(772)</text>
  </g>

  <!-- Line 9: client to server ACK -->
  <g id="ladder-line-9">
    <circle cx="515" cy="790" r="24" fill="#207448" />
    <text x="515" y="798" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">9</text>
    <!-- Arrow: client (695) to server (1335) -->
    <line x1="695" y1="790" x2="1335" y2="790" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <!-- Monospace packet label -->
    <text x="1015" y="776" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">. ack 773</text>
  </g>

  <!-- ==================== FLAG LEGEND ==================== -->
  <g id="panel-legend">
    <rect x="40" y="865" width="1520" height="60" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="903" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">S SYN, S. SYN-ACK, . ACK, P. PSH-ACK, F. FIN-ACK, R or R. RST</text>
  </g>

  <!-- ==================== FOOTER ==================== -->
  <g id="panel-footer">
    <rect x="40" y="965" width="1520" height="60" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <text x="800" y="1003" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">summary: 9 packets received by filter, 0 packets dropped by kernel</text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="panel-bottom-bar">
    <rect x="40" y="1065" width="1520" height="95" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />
    <text x="800" y="1103" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="800" dy="0">Read the flags in order; a SYN with no reply stops the story at the first line, </tspan>
      <tspan x="800" dy="34">and the next question is who stayed silent</tspan>
    </text>
  </g>
</svg>'''
    return svg

if __name__ == "__main__":
    content = create_svg()
    with open("candidate_read_conv.svg", "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote candidate_read_conv.svg")
