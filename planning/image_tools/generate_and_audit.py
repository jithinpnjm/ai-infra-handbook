import xml.etree.ElementTree as ET
import re, json, subprocess, pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1070" width="1600" height="1070">
  <title>Cluster autoscaler: pending pods, node groups and the settings that matter</title>
  <desc>Cluster autoscaler: pending pods, node groups and the settings that matter</desc>
  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1070" fill="#f5f8f5" />

  <!-- Title (48px bold, 2 lines) -->
  <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Cluster autoscaler: pending pods,</tspan>
    <tspan x="800" dy="54">node groups and the settings that matter</tspan>
  </text>

  <!-- ==================== LEFT COLUMN: FLOW & DASHBOARD NOTE ==================== -->
  <!-- Left Column Outer Container (subgraph) -->
  <rect x="40" y="125" width="580" height="890" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Box 1: HPA asks for more replicas -->
  <rect x="55" y="140" width="550" height="80" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: Gear / Autoscaling service -->
  <g transform="translate(70, 154)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="26" cy="26" r="10" />
    <path d="M 26 6 L 26 12 M 26 40 L 26 46 M 6 26 L 12 26 M 40 26 L 46 26 M 12 12 L 16 16 M 36 36 L 40 40 M 12 40 L 16 36 M 36 12 L 40 16" />
  </g>
  <text x="145" y="188" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="145" dy="0">HPA asks for more replicas</tspan>
  </text>

  <!-- Arrow 1 -> 2 -->
  <line x1="330" y1="220" x2="330" y2="258" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Box 2: pods sit Pending: no node has a free GPU -->
  <rect x="55" y="260" width="550" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: GPU chip with pause / wait -->
  <g transform="translate(70, 282)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="8" width="40" height="40" rx="4" />
    <line x1="18" y1="20" x2="18" y2="36" />
    <line x1="34" y1="20" x2="34" y2="36" />
    <line x1="12" y1="2" x2="12" y2="8" /><line x1="26" y1="2" x2="26" y2="8" /><line x1="40" y1="2" x2="40" y2="8" />
    <line x1="12" y1="48" x2="12" y2="54" /><line x1="26" y1="48" x2="26" y2="54" /><line x1="40" y1="48" x2="40" y2="54" />
  </g>
  <text x="145" y="306" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="145" dy="0">pods sit Pending:</tspan>
    <tspan x="145" dy="28">no node has a free GPU</tspan>
  </text>

  <!-- Arrow 2 -> 3 -->
  <line x1="330" y1="360" x2="330" y2="398" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Box 3: cluster autoscaler notices pending pods that a node group could fit -->
  <rect x="55" y="400" width="550" height="126" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: Radar / Autoscaler scanner -->
  <g transform="translate(70, 435)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="26" cy="26" r="20" />
    <circle cx="26" cy="26" r="10" />
    <line x1="26" y1="6" x2="26" y2="46" />
    <line x1="6" y1="26" x2="46" y2="26" />
    <polyline points="26,26 40,12" stroke-width="3" />
  </g>
  <text x="145" y="446" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="145" dy="0">cluster autoscaler notices</tspan>
    <tspan x="145" dy="28">pending pods that a node</tspan>
    <tspan x="145" dy="28">group could fit</tspan>
  </text>

  <!-- Arrow 3 -> 4 -->
  <line x1="330" y1="526" x2="330" y2="564" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Box 4: asks the cloud for a node; provisioning clock starts -->
  <rect x="55" y="566" width="550" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: Cloud with clock -->
  <g transform="translate(70, 588)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 8 36 C 4 36 2 32 4 28 C 4 24 8 22 12 22 C 14 14 26 12 32 18 C 36 14 44 16 46 22 C 50 24 52 28 50 32 C 50 36 46 36 44 36 Z" />
    <circle cx="26" cy="38" r="12" fill="#ffffff" />
    <polyline points="26,30 26,38 32,38" />
  </g>
  <text x="145" y="612" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="145" dy="0">asks the cloud for a node;</tspan>
    <tspan x="145" dy="28">provisioning clock starts</tspan>
  </text>

  <!-- Arrow 4 -> 5 -->
  <line x1="330" y1="666" x2="330" y2="704" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Box 5: node registers, image pull, weight load, ready -->
  <rect x="55" y="706" width="550" height="100" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: Server node with checkmark -->
  <g transform="translate(70, 728)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="8" width="40" height="36" rx="4" />
    <line x1="6" y1="20" x2="46" y2="20" />
    <circle cx="14" cy="14" r="2" fill="#207448" />
    <circle cx="22" cy="14" r="2" fill="#207448" />
    <polyline points="14,30 22,38 38,24" stroke="#207448" stroke-width="3.5" />
  </g>
  <text x="145" y="752" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="145" dy="0">node registers, image pull,</tspan>
    <tspan x="145" dy="28">weight load, ready</tspan>
  </text>

  <!-- Dashboard note: single most important item, highlighted in orange #db8129 -->
  <rect x="55" y="836" width="550" height="164" rx="12" fill="#fff9f3" stroke="#db8129" stroke-width="2.5" />
  <!-- Icon: Dashboard speedometer in orange -->
  <g transform="translate(70, 890)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 6 38 A 22 22 0 1 1 46 38" />
    <line x1="26" y1="38" x2="38" y2="20" />
    <circle cx="26" cy="38" r="3" fill="#db8129" />
  </g>
  <text x="145" y="880" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="145" dy="0">replica count rose at</tspan>
    <tspan x="145" dy="28">once while serving</tspan>
    <tspan x="145" dy="28">count stayed flat;</tspan>
    <tspan x="145" dy="28">that gap is what to explain</tspan>
  </text>

  <!-- ==================== RIGHT COLUMN: SETTINGS TABLE & NEBIUS NOTES ==================== -->
  <!-- Settings Table Container -->
  <rect x="660" y="125" width="900" height="615" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

  <!-- Card 1: expander chooses which node group to grow -->
  <rect x="675" y="140" width="870" height="126" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: Sliders / Branching choice -->
  <g transform="translate(692, 178)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <line x1="6" y1="12" x2="36" y2="12" /><circle cx="16" cy="12" r="4" fill="#207448" />
    <line x1="6" y1="24" x2="36" y2="24" /><circle cx="28" cy="24" r="4" fill="#207448" />
    <line x1="6" y1="36" x2="36" y2="36" /><circle cx="20" cy="36" r="4" fill="#207448" />
  </g>
  <text x="746" y="187" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="746" dy="0" font-weight="bold">expander chooses which node group to grow:</tspan>
    <tspan x="746" dy="28">random, most-pods, least-waste, price,</tspan>
    <tspan x="746" dy="28">priority (rank GPU types)</tspan>
  </text>

  <!-- Card 2: max-node-provision-time default 15 minutes -->
  <rect x="675" y="290" width="870" height="150" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: Timer / Stop watch -->
  <g transform="translate(692, 342)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="22" cy="24" r="16" />
    <polyline points="22,14 22,24 28,24" />
    <line x1="18" y1="4" x2="26" y2="4" />
    <line x1="22" y1="4" x2="22" y2="8" />
  </g>
  <text x="746" y="334" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="746" dy="0" font-family="monospace" font-weight="bold">--max-node-provision-time default 15 minutes:</tspan>
    <tspan x="746" dy="28">if a node has not registered by then</tspan>
    <tspan x="746" dy="28">the autoscaler stops counting it,</tspan>
    <tspan x="746" dy="28">which is why you keep warm capacity</tspan>
  </text>

  <!-- Card 3: scale-down: node considered when pod CPU and memory requests sum below 50 percent -->
  <rect x="675" y="460" width="870" height="260" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: Downward scale / drain -->
  <g transform="translate(692, 565)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="36" height="38" rx="4" />
    <line x1="4" y1="18" x2="40" y2="18" />
    <polyline points="14,26 22,34 30,26" />
    <line x1="22" y1="20" x2="22" y2="34" />
  </g>
  <text x="746" y="504" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="746" dy="0" font-weight="bold">scale-down: node considered when pod CPU and</tspan>
    <tspan x="746" dy="28">memory requests sum below 50 percent of allocatable;</tspan>
    <tspan x="746" dy="28">must stay unneeded 10 minutes; held 10 minutes after a</tspan>
    <tspan x="746" dy="28">scale-up; evicts through the eviction API for up to</tspan>
    <tspan x="746" dy="28">2 minutes; accelerator flag</tspan>
    <tspan x="746" dy="28" font-family="monospace" font-weight="bold">scale-down-gpu-utilization-threshold default 0.5</tspan>
  </text>

  <!-- Nebius Node Group Notes Container -->
  <rect x="660" y="760" width="900" height="255" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <rect x="675" y="775" width="870" height="225" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Icon: Cloud network / nodes -->
  <g transform="translate(692, 868)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="4" width="16" height="14" rx="2" />
    <rect x="24" y="4" width="16" height="14" rx="2" />
    <rect x="14" y="26" width="16" height="14" rx="2" />
    <line x1="12" y1="18" x2="12" y2="22" /><line x1="32" y1="18" x2="32" y2="22" />
    <line x1="12" y1="22" x2="32" y2="22" /><line x1="22" y1="22" x2="22" y2="26" />
  </g>
  <text x="746" y="817" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="746" dy="0" font-weight="bold">autoscaling min and max node count flags; page gives</tspan>
    <tspan x="746" dy="28">no defaults or timings; keep a CPU node group of at</tspan>
    <tspan x="746" dy="28">least two nodes (or autoscaling) so CoreDNS and</tspan>
    <tspan x="746" dy="28">networking add-ons run there; known issue with</tspan>
    <tspan x="746" dy="28">GPU Operator and Network Operator creating</tspan>
    <tspan x="746" dy="28">extra nodes, not reproduced</tspan>
  </text>
</svg>
'''

pathlib.Path("candidate_ca_generated.svg").write_text(svg_content)
print("Updated candidate_ca_generated.svg")
