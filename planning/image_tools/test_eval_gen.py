import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="960" viewBox="0 0 1600 960">
  <title>Pod addresses change, so clients need a stable name</title>
  <desc>Infographic explaining why Kubernetes clients require a stable Service name and virtual IP instead of ephemeral pod addresses.</desc>
  <defs>
    <marker id="arrow-green" markerWidth="14" markerHeight="14" refX="10" refY="7" orient="auto">
      <path d="M 1 2 L 11 7 L 1 12 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="960" fill="#f5f8f5" />

  <!-- Diagram Title -->
  <text x="800" y="70" font-family="sans-serif" font-size="48" font-weight="bold" fill="#207448" text-anchor="middle">Pod addresses change, so clients need a stable name</text>

  <!-- LEFT COLUMN: Client Box -->
  <rect x="50" y="130" width="410" height="670" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  
  <!-- Client Window Icon (56x56) -->
  <rect x="75" y="155" width="56" height="46" rx="6" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <line x1="75" y1="171" x2="131" y2="171" stroke="#207448" stroke-width="2" />
  <circle cx="87" cy="163" r="3" fill="#207448" />
  <circle cx="97" cy="163" r="3" fill="#207448" />
  <circle cx="107" cy="163" r="3" fill="#207448" />
  
  <text x="145" y="190" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Client</text>

  <!-- Memory Card: Remembered addresses -->
  <rect x="70" y="225" width="370" height="280" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  
  <!-- Memory Chip Icon -->
  <rect x="90" y="243" width="36" height="40" rx="4" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <line x1="98" y1="243" x2="98" y2="253" stroke="#207448" stroke-width="2" />
  <line x1="108" y1="243" x2="108" y2="253" stroke="#207448" stroke-width="2" />
  <line x1="118" y1="243" x2="118" y2="253" stroke="#207448" stroke-width="2" />
  
  <text x="138" y="272" font-family="sans-serif" font-size="25" font-weight="bold" fill="#207448">Remembered addresses</text>

  <!-- Old IP Box A -->
  <rect x="90" y="305" width="330" height="65" rx="8" fill="#f3f4f6" stroke="#9ca3af" stroke-width="2" />
  <text x="255" y="346" font-family="sans-serif" font-size="24" fill="#6b7280" text-anchor="middle">Pod IP A (old)</text>

  <!-- Old IP Box B -->
  <rect x="90" y="390" width="330" height="65" rx="8" fill="#f3f4f6" stroke="#9ca3af" stroke-width="2" />
  <text x="255" y="431" font-family="sans-serif" font-size="24" fill="#6b7280" text-anchor="middle">Pod IP B (old)</text>

  <!-- Red Cross over old addresses -->
  <line x1="105" y1="315" x2="405" y2="445" stroke="#dc2626" stroke-width="6" stroke-linecap="round" />
  <line x1="105" y1="445" x2="405" y2="315" stroke="#dc2626" stroke-width="6" stroke-linecap="round" />

  <!-- Note Panel: machines no longer exist -->
  <rect x="70" y="530" width="370" height="245" rx="12" fill="#fef2f2" stroke="#dc2626" stroke-width="2" />
  
  <!-- Alert icon (circle with !) -->
  <circle cx="255" cy="565" r="18" fill="#fee2e2" stroke="#dc2626" stroke-width="3" />
  <line x1="255" y1="554" x2="255" y2="568" stroke="#dc2626" stroke-width="3" stroke-linecap="round" />
  <circle cx="255" cy="575" r="2" fill="#dc2626" />

  <text x="255" y="625" font-family="sans-serif" font-size="24" font-weight="bold" fill="#b91c1c" text-anchor="middle">
    <tspan x="255" dy="0">These machines no</tspan>
    <tspan x="255" dy="34">longer exist, and</tspan>
    <tspan x="255" dy="34">nothing tells the client</tspan>
  </text>

  <!-- MIDDLE: Rollout Arrow -->
  <text x="600" y="440" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448" text-anchor="middle">
    <tspan x="600" dy="0">Rollout replaces</tspan>
    <tspan x="600" dy="30">the Pods</tspan>
  </text>
  <line x1="480" y1="490" x2="720" y2="490" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- MIDDLE COLUMN: Two New Pods -->
  <!-- New Pod C -->
  <rect x="740" y="225" width="280" height="220" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Pod Icon (container block) -->
  <rect x="852" y="250" width="56" height="50" rx="6" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <rect x="860" y="258" width="16" height="14" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <rect x="884" y="258" width="16" height="14" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <rect x="860" y="278" width="40" height="14" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <text x="880" y="360" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">New Pod C</text>

  <!-- New Pod D -->
  <rect x="740" y="490" width="280" height="220" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <!-- Pod Icon -->
  <rect x="852" y="515" width="56" height="50" rx="6" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <rect x="860" y="523" width="16" height="14" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <rect x="884" y="523" width="16" height="14" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <rect x="860" y="543" width="40" height="14" rx="2" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <text x="880" y="625" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">New Pod D</text>

  <!-- RIGHT COLUMN: Service Box (with Orange outline) -->
  <rect x="1220" y="225" width="330" height="485" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="4" />
  
  <!-- Gear Icon for Service (56x56) -->
  <circle cx="1385" cy="285" r="22" fill="#fef3e2" stroke="#207448" stroke-width="3" />
  <circle cx="1385" cy="285" r="10" fill="#ffffff" stroke="#207448" stroke-width="3" />
  <path d="M 1385 257 L 1385 263 M 1385 307 L 1385 313 M 1357 285 L 1363 285 M 1407 285 L 1413 285 M 1365 265 L 1370 270 M 1400 300 L 1405 305 M 1365 305 L 1370 300 M 1400 270 L 1405 265" stroke="#207448" stroke-width="3" stroke-linecap="round" />

  <text x="1385" y="380" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="1385" dy="0">Service:</tspan>
    <tspan x="1385" dy="40" font-size="25" font-weight="normal">stable virtual IP</tspan>
    <tspan x="1385" dy="36" font-size="25" font-weight="normal">and name</tspan>
  </text>

  <!-- Service to Pods Arrows: Ready endpoints -->
  <line x1="1220" y1="335" x2="1035" y2="335" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  <line x1="1220" y1="600" x2="1035" y2="600" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <text x="1125" y="460" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448" text-anchor="middle">
    <tspan x="1125" dy="0">Ready</tspan>
    <tspan x="1125" dy="30">endpoints</tspan>
  </text>

  <!-- BOTTOM: Caption / Takeaway Bar -->
  <rect x="50" y="840" width="1500" height="70" rx="12" fill="#207448" />
  <text x="800" y="884" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle">Service discovery answers: which processes listen at which addresses, for which service?</text>
</svg>
'''

with open("test_candidate_eval.svg", "w") as f:
    f.write(svg_content)

print("Saved test_candidate_eval.svg")
