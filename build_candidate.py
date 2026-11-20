#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>site.yml imports the tiers in dependency order</title>
  <desc>Visual infographic explaining how playbooks/site.yml imports the five tier playbooks in dependency order from baseline to verify.</desc>

  <defs>
    <!-- Green Arrowhead (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 z" fill="#207448"/>
    </marker>
    <!-- Orange Arrowhead (18px) -->
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 z" fill="#db8129"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="78" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">site.yml imports the tiers in dependency order</text>

  <!-- ==================== FILE CARD: playbooks/site.yml ==================== -->
  <g id="file-card-site">
    <rect x="470" y="130" width="660" height="190" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Card Header Tab -->
    <path d="M 470 142 Q 470 130 482 130 L 1118 130 Q 1130 130 1130 142 L 1130 167 L 470 167 Z" fill="#e8f1ea"/>
    <line x1="470" y1="167" x2="1130" y2="167" stroke="#207448" stroke-width="1.5"/>
    <!-- File icon -->
    <path d="M 492 140 h 14 l 6 6 v 13 h -20 z" fill="none" stroke="#207448" stroke-width="2" stroke-linejoin="round"/>
    <polyline points="506,140 506,146 512,146" fill="none" stroke="#207448" stroke-width="2"/>
    <!-- Card Title -->
    <text x="522" y="156" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" font-weight="bold" fill="#207448">playbooks/site.yml</text>
    <!-- 5 Code lines -->
    <text x="495" y="195" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" fill="#303a36">- import_playbook: baseline.yml</text>
    <text x="495" y="223" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" fill="#303a36">- import_playbook: database.yml</text>
    <text x="495" y="251" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" fill="#303a36">- import_playbook: app.yml</text>
    <text x="495" y="279" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" fill="#303a36">- import_playbook: web.yml</text>
    <text x="495" y="307" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" fill="#303a36">- import_playbook: verify.yml</text>
  </g>

  <!-- ==================== LEFT COLUMN NOTES (Monospace) ==================== -->
  <!-- Note beside Box 2: tags db runs only the tagged tier -->
  <g id="note-tags-db">
    <rect x="50" y="479" width="370" height="128" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" fill="#303a36">
      <tspan x="75" y="519" font-weight="bold" fill="#207448">--tags db</tspan>
      <tspan x="75" y="551">runs only the</tspan>
      <tspan x="75" y="583">tagged tier</tspan>
    </text>
    <!-- Connector line toward tier 2 -->
    <line x1="420" y1="543" x2="470" y2="543" stroke="#207448" stroke-width="2" stroke-dasharray="6,4"/>
  </g>

  <!-- Note beside Box 3: limit app limits the run to one host group -->
  <g id="note-limit-app">
    <rect x="50" y="615" width="370" height="128" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <text font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" fill="#303a36">
      <tspan x="75" y="655" font-weight="bold" fill="#207448">-l app</tspan>
      <tspan x="75" y="687">limits the run to</tspan>
      <tspan x="75" y="719">one host group</tspan>
    </text>
    <!-- Connector line toward tier 3 -->
    <line x1="420" y1="679" x2="470" y2="679" stroke="#207448" stroke-width="2" stroke-dasharray="6,4"/>
  </g>

  <!-- ==================== RIGHT COLUMN NOTES ==================== -->
  <!-- Arrow 2 to 3 Label (Orange highlight) -->
  <g id="label-db-app">
    <rect x="1170" y="547" width="390" height="128" rx="12" fill="#fff9f2" stroke="#db8129" stroke-width="2.5"/>
    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">
      <tspan x="1195" y="587">the database must exist</tspan>
      <tspan x="1195" y="619">before the app</tspan>
      <tspan x="1195" y="651">tries to connect</tspan>
    </text>
    <!-- Connector line to orange arrow 2->3 -->
    <line x1="800" y1="611" x2="1170" y2="611" stroke="#db8129" stroke-width="2" stroke-dasharray="6,4"/>
  </g>

  <!-- Note linking Box 3 and Box 4 -->
  <g id="label-app-web">
    <rect x="1170" y="683" width="390" height="128" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="1195" y="723">the app must answer</tspan>
      <tspan x="1195" y="755">before the proxy</tspan>
      <tspan x="1195" y="787">sends it traffic</tspan>
    </text>
    <!-- Orthogonal link bracket connecting Box 3 and Box 4 -->
    <path d="M 1130 679 H 1150 V 747 H 1170" fill="none" stroke="#207448" stroke-width="2" stroke-dasharray="6,4"/>
    <path d="M 1130 815 H 1150 V 747" fill="none" stroke="#207448" stroke-width="2" stroke-dasharray="6,4"/>
  </g>

  <!-- ==================== ARROWS BETWEEN BOXES ==================== -->
  <!-- Arrow 1 -> 2 -->
  <line x1="800" y1="454" x2="800" y2="496" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Arrow 2 -> 3 (ORANGE HIGHLIGHT) -->
  <line x1="800" y1="590" x2="800" y2="632" stroke="#db8129" stroke-width="5" marker-end="url(#arrow-orange)"/>

  <!-- Arrow 3 -> 4 -->
  <line x1="800" y1="726" x2="800" y2="768" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Arrow 4 -> 5 -->
  <line x1="800" y1="862" x2="800" y2="904" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- ==================== CHAIN OF FIVE BOXES ==================== -->
  <!-- BOX 1: baseline.yml -->
  <g id="box-1">
    <rect x="470" y="360" width="660" height="94" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Number circle 1 -->
    <circle cx="512" cy="407" r="24" fill="#207448"/>
    <text x="512" y="407" text-anchor="middle" dominant-baseline="central" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
    <!-- Server / OS Icon (56px) -->
    <g transform="translate(548, 379)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="44" rx="4"/>
      <line x1="4" y1="20" x2="52" y2="20"/>
      <circle cx="14" cy="13" r="2" fill="#207448"/>
      <circle cx="22" cy="13" r="2" fill="#207448"/>
      <polyline points="14,32 20,37 14,42"/>
      <line x1="26" y1="42" x2="38" y2="42"/>
    </g>
    <!-- Title -->
    <text x="620" y="398" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="30" font-weight="bold" fill="#303a36">baseline.yml</text>
    <!-- Tag badge: baseline -->
    <rect x="860" y="376" width="145" height="30" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="932" y="397" text-anchor="middle" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" font-weight="bold" fill="#207448">baseline</text>
    <!-- Note -->
    <text x="620" y="432" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">OS baseline on every host</text>
  </g>

  <!-- BOX 2: database.yml -->
  <g id="box-2">
    <rect x="470" y="496" width="660" height="94" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Number circle 2 -->
    <circle cx="512" cy="543" r="24" fill="#207448"/>
    <text x="512" y="543" text-anchor="middle" dominant-baseline="central" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
    <!-- Database Cylinder Icon (56px) -->
    <g transform="translate(548, 515)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="22" ry="8"/>
      <path d="M 6 14 v 24 c 0 6 10 9 22 9 s 22 -3 22 -9 v -24"/>
      <path d="M 6 26 c 0 6 10 9 22 9 s 22 -3 22 -9"/>
    </g>
    <!-- Title -->
    <text x="620" y="534" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="30" font-weight="bold" fill="#303a36">database.yml</text>
    <!-- Tag badge: db -->
    <rect x="860" y="512" width="60" height="30" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="890" y="533" text-anchor="middle" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" font-weight="bold" fill="#207448">db</text>
    <!-- Note -->
    <text x="620" y="568" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">PostgreSQL on the db group</text>
  </g>

  <!-- BOX 3: app.yml -->
  <g id="box-3">
    <rect x="470" y="632" width="660" height="94" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Number circle 3 -->
    <circle cx="512" cy="679" r="24" fill="#207448"/>
    <text x="512" y="679" text-anchor="middle" dominant-baseline="central" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
    <!-- Application Window Icon (56px) -->
    <g transform="translate(548, 651)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="44" rx="6"/>
      <line x1="4" y1="18" x2="52" y2="18" stroke-width="3"/>
      <circle cx="12" cy="12" r="2" fill="#207448"/>
      <circle cx="18" cy="12" r="2" fill="#207448"/>
      <circle cx="24" cy="12" r="2" fill="#207448"/>
      <rect x="12" y="26" width="14" height="16" rx="2" stroke-width="2.5"/>
      <line x1="32" y1="28" x2="44" y2="28" stroke-width="2.5"/>
      <line x1="32" y1="36" x2="44" y2="36" stroke-width="2.5"/>
    </g>
    <!-- Title -->
    <text x="620" y="670" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="30" font-weight="bold" fill="#303a36">app.yml</text>
    <!-- Tag badge: app -->
    <rect x="765" y="648" width="75" height="30" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="802" y="669" text-anchor="middle" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" font-weight="bold" fill="#207448">app</text>
    <!-- Note -->
    <text x="620" y="704" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">application on the app group</text>
  </g>

  <!-- BOX 4: web.yml -->
  <g id="box-4">
    <rect x="470" y="768" width="660" height="94" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Number circle 4 -->
    <circle cx="512" cy="815" r="24" fill="#207448"/>
    <text x="512" y="815" text-anchor="middle" dominant-baseline="central" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
    <!-- Reverse Proxy / Network Globe Icon (56px) -->
    <g transform="translate(548, 787)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <ellipse cx="28" cy="28" rx="10" ry="22" stroke-width="3"/>
      <line x1="6" y1="28" x2="50" y2="28" stroke-width="3"/>
      <line x1="12" y1="16" x2="44" y2="16" stroke-width="2.5"/>
      <line x1="12" y1="40" x2="44" y2="40" stroke-width="2.5"/>
    </g>
    <!-- Title -->
    <text x="620" y="806" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="30" font-weight="bold" fill="#303a36">web.yml</text>
    <!-- Tag badge: web -->
    <rect x="765" y="784" width="75" height="30" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="802" y="805" text-anchor="middle" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" font-weight="bold" fill="#207448">web</text>
    <!-- Note -->
    <text x="620" y="840" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">nginx reverse proxy</text>
  </g>

  <!-- BOX 5: verify.yml -->
  <g id="box-5">
    <rect x="470" y="904" width="660" height="94" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Number circle 5 -->
    <circle cx="512" cy="951" r="24" fill="#207448"/>
    <text x="512" y="951" text-anchor="middle" dominant-baseline="central" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
    <!-- Verification Shield Icon (56px) -->
    <g transform="translate(548, 923)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 40 28 50 28 50 C 28 50 8 40 8 28 V 14 Z"/>
      <polyline points="18,28 25,35 38,20"/>
    </g>
    <!-- Title -->
    <text x="620" y="942" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="30" font-weight="bold" fill="#303a36">verify.yml</text>
    <!-- Tag badge: verify -->
    <rect x="805" y="920" width="115" height="30" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    <text x="862" y="941" text-anchor="middle" font-family="'SF Mono', 'Courier New', Courier, Consolas, monospace" font-size="24" font-weight="bold" fill="#207448">verify</text>
    <!-- Note -->
    <text x="620" y="976" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">end-to-end verification</text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="1038" width="1520" height="110" rx="12" fill="#207448"/>
    <text font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">
      <tspan x="800" y="1081">The database must exist before the app tries to connect,</tspan>
      <tspan x="800" y="1119">and the app must answer before the proxy sends it traffic.</tspan>
    </text>
  </g>
</svg>"""

with open('output_candidate.svg', 'w') as f:
    f.write(svg_content)

print("Candidate SVG updated successfully")
