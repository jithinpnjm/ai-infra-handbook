import re
import xml.etree.ElementTree as ET

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1150" width="1600" height="1150">
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
  <rect width="1600" height="1150" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Two writers and a 409 Conflict</text>

  <!-- ==================== PARTICIPANT HEADERS ==================== -->

  <!-- Lifeline 1: Client A -->
  <g id="header-client-a">
    <rect x="90" y="80" width="300" height="130" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Application Window Icon (56px) -->
    <g transform="translate(212, 92)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="56" height="42" rx="5" />
      <line x1="0" y1="12" x2="56" y2="12" />
      <circle cx="10" cy="6" r="2" fill="#207448" />
      <circle cx="18" cy="6" r="2" fill="#207448" />
      <circle cx="26" cy="6" r="2" fill="#207448" />
    </g>
    <text x="240" y="188" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Client A</text>
  </g>

  <!-- Lifeline 2: kube-apiserver / etcd -->
  <g id="header-apiserver-etcd">
    <rect x="520" y="80" width="560" height="130" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Gear & Storage Icon (56px) -->
    <g transform="translate(772, 92)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="2" width="48" height="40" rx="4" />
      <line x1="4" y1="14" x2="52" y2="14" />
      <line x1="4" y1="28" x2="52" y2="28" />
      <circle cx="14" cy="8" r="2" fill="#207448" />
      <circle cx="14" cy="21" r="2" fill="#207448" />
      <circle cx="14" cy="35" r="2" fill="#207448" />
      <line x1="26" y1="8" x2="44" y2="8" />
      <line x1="26" y1="21" x2="44" y2="21" />
      <line x1="26" y1="35" x2="44" y2="35" />
    </g>
    <text x="800" y="188" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">kube-apiserver / etcd</text>
  </g>

  <!-- Lifeline 3: Client B -->
  <g id="header-client-b">
    <rect x="1210" y="80" width="300" height="130" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Application Window Icon (56px) -->
    <g transform="translate(1332, 92)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="56" height="42" rx="5" />
      <line x1="0" y1="12" x2="56" y2="12" />
      <circle cx="10" cy="6" r="2" fill="#207448" />
      <circle cx="18" cy="6" r="2" fill="#207448" />
      <circle cx="26" cy="6" r="2" fill="#207448" />
    </g>
    <text x="1360" y="188" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Client B</text>
  </g>

  <!-- ==================== VERTICAL LIFELINES ==================== -->
  <line x1="240" y1="210" x2="240" y2="940" stroke="#a3b899" stroke-width="3" stroke-dasharray="8 6" />
  <line x1="800" y1="210" x2="800" y2="940" stroke="#a3b899" stroke-width="3" stroke-dasharray="8 6" />
  <line x1="1360" y1="210" x2="1360" y2="940" stroke="#a3b899" stroke-width="3" stroke-dasharray="8 6" />

  <!-- ==================== STEP 1 ==================== -->
  <!-- 1 Client A reads object at resourceVersion 5012. -->
  <g id="step-1">
    <rect x="280" y="222" width="480" height="66" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="520" y="249" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="520" dy="0">Client A reads object at</tspan>
      <tspan x="520" dy="28">resourceVersion 5012.</tspan>
    </text>
    <circle cx="240" cy="302" r="24" fill="#207448" />
    <text x="240" y="311" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <line x1="264" y1="302" x2="800" y2="302" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  </g>

  <!-- ==================== STEP 2 ==================== -->
  <!-- 2 Client B reads the same object at resourceVersion 5012. -->
  <g id="step-2">
    <rect x="840" y="340" width="480" height="66" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1080" y="367" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1080" dy="0">Client B reads the same object</tspan>
      <tspan x="1080" dy="28">at resourceVersion 5012.</tspan>
    </text>
    <circle cx="1360" cy="420" r="24" fill="#207448" />
    <text x="1360" y="429" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <line x1="1336" y1="420" x2="800" y2="420" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green-left)" />
  </g>

  <!-- ==================== STEP 3 ==================== -->
  <!-- 3 Client B writes its change; server accepts; object now at resourceVersion 5013. -->
  <g id="step-3">
    <rect x="840" y="460" width="480" height="94" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1080" y="488" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1080" dy="0">Client B writes its change;</tspan>
      <tspan x="1080" dy="28">server accepts; object now at</tspan>
      <tspan x="1080" dy="28">resourceVersion 5013.</tspan>
    </text>
    <circle cx="1360" cy="568" r="24" fill="#207448" />
    <text x="1360" y="577" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <line x1="1336" y1="568" x2="800" y2="568" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green-left)" />
  </g>

  <!-- ==================== STEP 4 ==================== -->
  <!-- 4 Client A writes its change based on 5012; server rejects with HTTP 409 Conflict (red). -->
  <g id="step-4">
    <rect x="280" y="610" width="480" height="94" rx="10" fill="#fff9f2" stroke="#db8129" stroke-width="2.5" />
    <text x="520" y="638" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="520" dy="0">Client A writes its change</tspan>
      <tspan x="520" dy="28">based on 5012; server rejects</tspan>
      <tspan x="520" dy="28" font-weight="bold">with HTTP 409 Conflict.</tspan>
    </text>
    <circle cx="240" cy="718" r="24" fill="#207448" />
    <text x="240" y="727" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <line x1="264" y1="718" x2="800" y2="718" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />
  </g>

  <!-- ==================== STEP 5 ==================== -->
  <!-- 5 Client A re-reads the latest version from its informer cache, re-applies its change and retries (green). -->
  <g id="step-5">
    <rect x="280" y="756" width="480" height="122" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="520" y="784" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="520" dy="0">Client A re-reads the</tspan>
      <tspan x="520" dy="28">latest version from its</tspan>
      <tspan x="520" dy="28">informer cache, re-applies</tspan>
      <tspan x="520" dy="28">its change and retries.</tspan>
    </text>
    <circle cx="240" cy="892" r="24" fill="#207448" />
    <text x="240" y="901" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>
    <line x1="264" y1="892" x2="800" y2="892" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  </g>

  <!-- ==================== SIDE NOTES ==================== -->

  <!-- Side Note 1: resourceVersion maps to the etcd key mod_revision -->
  <g id="note-mod-revision">
    <rect x="80" y="970" width="680" height="130" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Database / Cylinder Icon (56px) -->
    <g transform="translate(105, 1007)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="24" ry="8" />
      <path d="M 4 14 v 28 c 0 4.4 10.7 8 24 8 s 24 -3.6 24 -8 v -28" />
      <path d="M 4 28 c 0 4.4 10.7 8 24 8 s 24 -3.6 24 -8" />
    </g>
    <text x="440" y="1030" text-anchor="middle" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="440" dy="0">resourceVersion maps to the</tspan>
      <tspan x="440" dy="34">etcd key mod_revision</tspan>
    </text>
  </g>

  <!-- Side Note 2: Server-side apply tracks field ownership in managedFields -->
  <g id="note-managed-fields">
    <rect x="840" y="970" width="680" height="130" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Shield / Security Icon (56px) -->
    <g transform="translate(865, 1007)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 10 L 28 4 L 46 10 C 46 32 28 48 28 48 C 28 48 10 32 10 10 Z" />
      <path d="M 20 25 L 26 31 L 37 19" />
    </g>
    <text x="1200" y="1030" text-anchor="middle" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="1200" dy="0">Server-side apply tracks field</tspan>
      <tspan x="1200" dy="34">ownership in managedFields</tspan>
    </text>
  </g>
</svg>'''

with open("test_candidate_conflict.svg", "w") as f:
    f.write(svg_code)

print("Saved test_candidate_conflict.svg")
