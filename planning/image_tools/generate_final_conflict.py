import re
import xml.etree.ElementTree as ET

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Two writers and a 409 Conflict</title>
  <desc>Sequence diagram illustrating optimistic concurrency control and HTTP 409 Conflict resolution between two clients and kube-apiserver with etcd.</desc>

  <defs>
    <!-- Arrowhead Green Right (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <!-- Arrowhead Green Left (18px) -->
    <marker id="arrow-green-left" viewBox="0 0 18 18" refX="2" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 16 3 L 2 9 L 16 15 Z" fill="#207448" />
    </marker>
    <!-- Arrowhead Orange Right (18px) -->
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="50" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Two writers and a 409 Conflict</text>

  <!-- ==================== PARTICIPANT HEADERS ==================== -->

  <!-- Lifeline 1: Client A -->
  <g id="header-client-a">
    <rect x="90" y="70" width="300" height="115" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Application Window Icon (56px) -->
    <g transform="translate(212, 79)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="56" height="40" rx="5" />
      <line x1="0" y1="12" x2="56" y2="12" />
      <circle cx="10" cy="6" r="2" fill="#207448" />
      <circle cx="18" cy="6" r="2" fill="#207448" />
      <circle cx="26" cy="6" r="2" fill="#207448" />
    </g>
    <text x="240" y="165" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Client A</text>
  </g>

  <!-- Lifeline 2: kube-apiserver / etcd -->
  <g id="header-apiserver-etcd">
    <rect x="520" y="70" width="560" height="115" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Gear & Storage Icon (56px) -->
    <g transform="translate(772, 79)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="2" width="48" height="38" rx="4" />
      <line x1="4" y1="14" x2="52" y2="14" />
      <line x1="4" y1="26" x2="52" y2="26" />
      <circle cx="14" cy="8" r="2" fill="#207448" />
      <circle cx="14" cy="20" r="2" fill="#207448" />
      <circle cx="14" cy="32" r="2" fill="#207448" />
      <line x1="26" y1="8" x2="44" y2="8" />
      <line x1="26" y1="20" x2="44" y2="20" />
      <line x1="26" y1="32" x2="44" y2="32" />
    </g>
    <text x="800" y="165" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">kube-apiserver / etcd</text>
  </g>

  <!-- Lifeline 3: Client B -->
  <g id="header-client-b">
    <rect x="1210" y="70" width="300" height="115" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Application Window Icon (56px) -->
    <g transform="translate(1332, 79)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="56" height="40" rx="5" />
      <line x1="0" y1="12" x2="56" y2="12" />
      <circle cx="10" cy="6" r="2" fill="#207448" />
      <circle cx="18" cy="6" r="2" fill="#207448" />
      <circle cx="26" cy="6" r="2" fill="#207448" />
    </g>
    <text x="1360" y="165" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Client B</text>
  </g>

  <!-- ==================== VERTICAL LIFELINES ==================== -->
  <line x1="240" y1="185" x2="240" y2="1025" stroke="#a3b899" stroke-width="3" stroke-dasharray="8 6" />
  <line x1="800" y1="185" x2="800" y2="1025" stroke="#a3b899" stroke-width="3" stroke-dasharray="8 6" />
  <line x1="1360" y1="185" x2="1360" y2="1025" stroke="#a3b899" stroke-width="3" stroke-dasharray="8 6" />

  <!-- ==================== STEP 1 ==================== -->
  <!-- 1 Client A reads object at resourceVersion 5012. -->
  <g id="step-1">
    <rect x="280" y="205" width="480" height="84" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="520" y="239" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="520" dy="0">Client A reads object at</tspan>
      <tspan x="520" dy="28">resourceVersion 5012.</tspan>
    </text>
    <circle cx="240" cy="307" r="24" fill="#207448" />
    <text x="240" y="316" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <line x1="264" y1="307" x2="800" y2="307" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  </g>

  <!-- ==================== STEP 2 ==================== -->
  <!-- 2 Client B reads the same object at resourceVersion 5012. -->
  <g id="step-2">
    <rect x="840" y="350" width="480" height="84" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1080" y="384" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1080" dy="0">Client B reads the same object</tspan>
      <tspan x="1080" dy="28">at resourceVersion 5012.</tspan>
    </text>
    <circle cx="1360" cy="452" r="24" fill="#207448" />
    <text x="1360" y="461" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <line x1="1336" y1="452" x2="800" y2="452" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green-left)" />
  </g>

  <!-- ==================== STEP 3 ==================== -->
  <!-- 3 Client B writes its change; server accepts; object now at resourceVersion 5013. -->
  <g id="step-3">
    <rect x="840" y="495" width="480" height="112" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1080" y="529" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1080" dy="0">Client B writes its change;</tspan>
      <tspan x="1080" dy="28">server accepts; object now at</tspan>
      <tspan x="1080" dy="28">resourceVersion 5013.</tspan>
    </text>
    <circle cx="1360" cy="625" r="24" fill="#207448" />
    <text x="1360" y="634" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <line x1="1336" y1="625" x2="800" y2="625" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green-left)" />
  </g>

  <!-- ==================== STEP 4 ==================== -->
  <!-- 4 Client A writes its change based on 5012; server rejects with HTTP 409 Conflict (red). -->
  <g id="step-4">
    <rect x="280" y="665" width="480" height="112" rx="10" fill="#fff9f2" stroke="#db8129" stroke-width="2.5" />
    <text x="520" y="699" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="520" dy="0">Client A writes its change</tspan>
      <tspan x="520" dy="28">based on 5012; server rejects</tspan>
      <tspan x="520" dy="28" font-weight="bold">with HTTP 409 Conflict.</tspan>
    </text>
    <circle cx="240" cy="795" r="24" fill="#207448" />
    <text x="240" y="804" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <line x1="264" y1="795" x2="800" y2="795" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />
  </g>

  <!-- ==================== STEP 5 ==================== -->
  <!-- 5 Client A re-reads the latest version from its informer cache, re-applies its change and retries (green). -->
  <g id="step-5">
    <rect x="280" y="835" width="480" height="140" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="520" y="869" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="520" dy="0">Client A re-reads the</tspan>
      <tspan x="520" dy="28">latest version from its</tspan>
      <tspan x="520" dy="28">informer cache, re-applies</tspan>
      <tspan x="520" dy="28">its change and retries.</tspan>
    </text>
    <circle cx="240" cy="993" r="24" fill="#207448" />
    <text x="240" y="1002" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>
    <line x1="264" y1="993" x2="800" y2="993" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  </g>

  <!-- ==================== SIDE NOTES ==================== -->

  <!-- Side Note 1: resourceVersion maps to the etcd key mod_revision -->
  <g id="note-mod-revision">
    <rect x="80" y="1045" width="680" height="130" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Database / Cylinder Icon (56px) -->
    <g transform="translate(105, 1082)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="24" ry="8" />
      <path d="M 4 14 v 28 c 0 4.4 10.7 8 24 8 s 24 -3.6 24 -8 v -28" />
      <path d="M 4 28 c 0 4.4 10.7 8 24 8 s 24 -3.6 24 -8" />
    </g>
    <text x="445" y="1105" text-anchor="middle" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="445" dy="0">resourceVersion maps to the</tspan>
      <tspan x="445" dy="34">etcd key mod_revision</tspan>
    </text>
  </g>

  <!-- Side Note 2: Server-side apply tracks field ownership in managedFields -->
  <g id="note-managed-fields">
    <rect x="840" y="1045" width="680" height="130" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Shield / Security Icon (56px) -->
    <g transform="translate(865, 1082)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 10 L 28 4 L 46 10 C 46 32 28 48 28 48 C 28 48 10 32 10 10 Z" />
      <path d="M 20 25 L 26 31 L 37 19" />
    </g>
    <text x="1205" y="1105" text-anchor="middle" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="1205" dy="0">Server-side apply tracks field</tspan>
      <tspan x="1205" dy="34">ownership in managedFields</tspan>
    </text>
  </g>
</svg>'''

with open("candidate_final_conflict.svg", "w") as f:
    f.write(svg_code)

print("Generated candidate_final_conflict.svg")
