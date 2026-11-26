#!/usr/bin/env python3
import pathlib

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>SSH forwards compared: which side listens and where traffic goes</title>
  <desc>Visual comparison of SSH local (-L), remote (-R), and dynamic (-D) port forwarding showing which side listens, where traffic goes, and forwarding commands.</desc>

  <defs>
    <!-- Green arrowhead (18px) -->
    <marker id="arrow" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- ==================== TITLE (48px bold) ==================== -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">SSH forwards compared:</tspan>
    <tspan x="800" dy="56">which side listens and where traffic goes</tspan>
  </text>

  <!-- ==================== HEADER ROW CONTAINER ==================== -->
  <g id="header-container">
    <rect x="60" y="140" width="1480" height="155" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Machine Box Left: Your machine -->
    <rect x="80" y="148" width="410" height="64" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Laptop / Client Workstation Icon (56px, stroke 4) -->
    <g transform="translate(95, 152)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="6" width="40" height="28" rx="3" />
      <line x1="2" y1="42" x2="54" y2="42" stroke-width="5" />
      <line x1="22" y1="42" x2="34" y2="42" stroke-width="4" />
      <line x1="14" y1="20" x2="26" y2="20" stroke-width="2.5" />
    </g>
    <text x="310" y="194" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Your machine</text>

    <!-- Thick Connection Line between Machine Boxes -->
    <line x1="490" y1="180" x2="1110" y2="180" stroke="#207448" stroke-width="8" stroke-linecap="round" />

    <!-- Pill Badge on Connection Line: SSH connection, port 22 -->
    <rect x="600" y="151" width="400" height="58" rx="14" fill="#207448" />
    <text x="800" y="191" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">SSH connection, port 22</text>

    <!-- Machine Box Right: Server -->
    <rect x="1110" y="148" width="410" height="64" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Server Rack Icon (56px, stroke 4) -->
    <g transform="translate(1125, 152)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="4" width="44" height="20" rx="3" />
      <rect x="6" y="28" width="44" height="20" rx="3" />
      <circle cx="14" cy="14" r="2.5" fill="#207448" />
      <circle cx="22" cy="14" r="2.5" fill="#207448" />
      <circle cx="14" cy="38" r="2.5" fill="#207448" />
      <circle cx="22" cy="38" r="2.5" fill="#207448" />
      <line x1="32" y1="14" x2="42" y2="14" stroke-width="3" />
      <line x1="32" y1="38" x2="42" y2="38" stroke-width="3" />
    </g>
    <text x="1330" y="194" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Server</text>

    <!-- Questions Row inside Header Container -->
    <!-- Question 1: Which side listens? -->
    <rect x="80" y="222" width="690" height="64" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="425" y="268" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Which side listens?</text>

    <!-- Question 2: Where does the traffic go? -->
    <rect x="830" y="222" width="690" height="64" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="1175" y="268" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Where does the traffic go?</text>
  </g>

  <!-- ==================== LANE 1: -L LOCAL FORWARD ==================== -->
  <g id="lane-1">
    <!-- Lane Container -->
    <rect x="60" y="335" width="1480" height="210" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Lane 1 Header: Title & Command -->
    <rect x="80" y="347" width="320" height="60" rx="8" fill="#e8f1ea" />
    <text x="240" y="391" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">-L local forward</text>

    <rect x="420" y="349" width="560" height="56" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <text x="700" y="389" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">ssh -L 6006:localhost:6006 gpu01</text>

    <!-- Left Box: Listening Socket Marker (ORANGE HIGHLIGHT - Lane 1 only!) -->
    <rect x="80" y="417" width="350" height="116" rx="12" fill="#fff5eb" stroke="#db8129" stroke-width="3" />
    <text x="255" y="482" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#db8129">listens on 6006</text>

    <!-- Central SSH Channel & Traffic Arrow (Left to Right, runs above note) -->
    <line x1="430" y1="435" x2="1120" y2="435" stroke="#207448" stroke-width="6" stroke-dasharray="8 6" />
    <line x1="440" y1="435" x2="1110" y2="435" stroke="#207448" stroke-width="5" marker-end="url(#arrow)" />

    <!-- Note Box (Center below SSH line) -->
    <rect x="520" y="448" width="510" height="84" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="1.5" />
    <text x="775" y="488" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="775" dy="0">open http://localhost:6006</tspan>
      <tspan x="775" dy="26">to reach TensorBoard</tspan>
    </text>

    <!-- Right Box: Destination on Server -->
    <rect x="1120" y="417" width="400" height="116" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="1320" y="481" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">localhost:6006 on gpu01</text>
  </g>

  <!-- ==================== LANE 2: -R REMOTE FORWARD ==================== -->
  <g id="lane-2">
    <!-- Lane Container -->
    <rect x="60" y="585" width="1480" height="210" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Lane 2 Header: Title & Command -->
    <rect x="80" y="597" width="320" height="60" rx="8" fill="#e8f1ea" />
    <text x="240" y="641" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">-R remote forward</text>

    <rect x="420" y="599" width="580" height="56" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <text x="710" y="639" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">ssh -R 9000:localhost:8000 server</text>

    <!-- Left Box: Destination on Your Machine -->
    <rect x="80" y="667" width="420" height="116" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="290" y="718" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="290" dy="0">localhost:8000</tspan>
      <tspan x="290" dy="32">on your machine</tspan>
    </text>

    <!-- Central SSH Channel & Traffic Arrow (Right to Left) -->
    <line x1="500" y1="725" x2="1100" y2="725" stroke="#207448" stroke-width="6" stroke-dasharray="8 6" />
    <line x1="1090" y1="725" x2="510" y2="725" stroke="#207448" stroke-width="5" marker-end="url(#arrow)" />

    <!-- Right Box: Listening Socket Marker on Server -->
    <rect x="1100" y="667" width="420" height="116" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="1310" y="732" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">listens on 9000</text>
  </g>

  <!-- ==================== LANE 3: -D DYNAMIC FORWARD ==================== -->
  <g id="lane-3">
    <!-- Lane Container -->
    <rect x="60" y="835" width="1480" height="210" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Lane 3 Header: Title & Command -->
    <rect x="80" y="847" width="336" height="60" rx="8" fill="#e8f1ea" />
    <text x="248" y="891" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">-D dynamic forward</text>

    <rect x="436" y="849" width="420" height="56" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <text x="646" y="889" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">ssh -D 1080 bastion</text>

    <!-- Left Box: Listening Socket Marker (SOCKS proxy) -->
    <rect x="80" y="917" width="420" height="116" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="290" y="982" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">SOCKS proxy on 1080</text>

    <!-- Central SSH Channel & Traffic Arrow (Left to Right through Bastion) -->
    <line x1="500" y1="975" x2="1050" y2="975" stroke="#207448" stroke-width="6" stroke-dasharray="8 6" />
    <line x1="510" y1="975" x2="1040" y2="975" stroke="#207448" stroke-width="5" marker-end="url(#arrow)" />

    <!-- Right Box: Destination via Bastion to Any Destination -->
    <rect x="1050" y="917" width="470" height="116" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="1285" y="968" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="1285" dy="0">traffic goes through bastion</tspan>
      <tspan x="1285" dy="30">to any destination</tspan>
    </text>
  </g>

  <!-- ==================== FOOTER NOTE ==================== -->
  <rect x="60" y="1085" width="1480" height="70" rx="14" fill="#207448" />
  <text x="800" y="1129" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#ffffff">-N -f: no remote command, go to background</text>
</svg>'''

dst = pathlib.Path("test_ssh_candidate.svg")
dst.write_text(svg_code)
print("Updated SVG written to test_ssh_candidate.svg")
'''
'''
