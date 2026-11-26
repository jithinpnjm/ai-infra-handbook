import xml.etree.ElementTree as ET
import re
import sys

svg_template = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">
  <title>Changing a record safely: lower the TTL first, and remember negative caching</title>
  <desc>Visual infographic explaining how to change a DNS record safely by lowering the TTL at least one interval ahead, negative caching of NXDOMAIN, and incrementing the SOA serial for secondaries.</desc>

  <!-- Background -->
  <rect width="1600" height="1180" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Changing a record safely:</tspan>
    <tspan x="800" dy="54">lower the TTL first, and remember negative caching</tspan>
  </text>

  <!-- ==================== TIMELINE SECTION ==================== -->
  <g id="timeline-container">
    <!-- Main Outer Container Panel -->
    <rect x="40" y="135" width="1520" height="395" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

    <!-- Timeline track line across nodes -->
    <line x1="65" y1="230" x2="1535" y2="230" stroke="#b8c9c0" stroke-width="4" stroke-dasharray="8 6" />

    <!-- Card 1: Marker T0 -->
    <g id="marker-t0">
      <rect x="55" y="155" width="300" height="275" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Timer / Clock Icon (56px) -->
      <g transform="translate(177, 170)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22" />
        <polyline points="28,14 28,28 38,28" />
        <line x1="22" y1="2" x2="34" y2="2" />
      </g>
      <text x="205" y="260" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="205" dy="0" font-weight="bold">T0: old TTL, say</tspan>
        <tspan x="205" dy="32">3600 s, caches</tspan>
        <tspan x="205" dy="32">worldwide hold the</tspan>
        <tspan x="205" dy="32">old answer for up</tspan>
        <tspan x="205" dy="32">to that long</tspan>
      </text>
    </g>

    <!-- Card 2: Step 1 -->
    <g id="step-1">
      <rect x="370" y="155" width="310" height="275" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Number Circle (r=24) -->
      <circle cx="410" cy="195" r="24" fill="#207448" />
      <text x="410" y="195" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
      <!-- Gauge / Lower-down slider Icon (56px) -->
      <g transform="translate(500, 168)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="44" height="40" rx="4" />
        <line x1="14" y1="28" x2="42" y2="28" />
        <polyline points="22,36 28,42 34,36" />
        <line x1="28" y1="16" x2="28" y2="42" />
      </g>
      <text x="525" y="265" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="525" dy="0" font-weight="bold">lower the TTL well</tspan>
        <tspan x="525" dy="34">before the change,</tspan>
        <tspan x="525" dy="34">at least one old-TTL</tspan>
        <tspan x="525" dy="34">interval earlier</tspan>
      </text>
    </g>

    <!-- Card 3: Marker Elapsed (Orange highlight) -->
    <g id="marker-elapsed">
      <rect x="695" y="155" width="325" height="275" rx="12" fill="#e8f1ea" stroke="#db8129" stroke-width="3.5" />
      <!-- Hourglass / Timer elapsed Icon (56px, orange) -->
      <g transform="translate(830, 168)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 12 8 L 44 8 L 32 26 L 44 44 L 12 44 L 24 26 Z" />
        <line x1="18" y1="40" x2="38" y2="40" />
      </g>
      <text x="857" y="265" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="857" dy="0" font-weight="bold" fill="#db8129">old TTL has elapsed:</tspan>
        <tspan x="857" dy="34">caches have</tspan>
        <tspan x="857" dy="34">forgotten, all now</tspan>
        <tspan x="857" dy="34">use the short TTL</tspan>
      </text>
    </g>

    <!-- Card 4: Step 2 -->
    <g id="step-2">
      <rect x="1035" y="155" width="175" height="275" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Number Circle (r=24) -->
      <circle cx="1122" cy="195" r="24" fill="#207448" />
      <text x="1122" y="195" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
      <!-- Network switch / IP swap Icon (56px) -->
      <g transform="translate(1094, 230)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="12" width="48" height="32" rx="4" />
        <circle cx="16" cy="28" r="3" fill="#207448" />
        <circle cx="28" cy="28" r="3" fill="#207448" />
        <circle cx="40" cy="28" r="3" fill="#207448" />
      </g>
      <text x="1122" y="325" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
        <tspan x="1122" dy="0">switch</tspan>
        <tspan x="1122" dy="34">the IP</tspan>
      </text>
    </g>

    <!-- Card 5: Step 3 -->
    <g id="step-3">
      <rect x="1225" y="155" width="140" height="275" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Number Circle (r=24) -->
      <circle cx="1295" cy="195" r="24" fill="#207448" />
      <text x="1295" y="195" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
      <!-- Pause / Hourglass waiting Icon (56px) -->
      <g transform="translate(1267, 230)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="20" />
        <line x1="23" y1="20" x2="23" y2="36" />
        <line x1="33" y1="20" x2="33" y2="36" />
      </g>
      <text x="1295" y="340" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">wait</text>
    </g>

    <!-- Card 6: Step 4 -->
    <g id="step-4">
      <rect x="1380" y="155" width="165" height="275" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Number Circle (r=24) -->
      <circle cx="1462" cy="195" r="24" fill="#207448" />
      <text x="1462" y="195" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
      <!-- Restore / Up slider Icon (56px) -->
      <g transform="translate(1434, 230)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="44" height="40" rx="4" />
        <line x1="14" y1="28" x2="42" y2="28" />
        <polyline points="22,20 28,14 34,20" />
        <line x1="28" y1="14" x2="28" y2="40" />
      </g>
      <text x="1462" y="325" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
        <tspan x="1462" dy="0">restore</tspan>
        <tspan x="1462" dy="34">the TTL</tspan>
      </text>
    </g>

    <!-- Trade-off Bar Under Timeline -->
    <g id="trade-off-bar">
      <rect x="55" y="450" width="1490" height="64" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Balance / Scale Icon (56px) -->
      <g transform="translate(80, 454)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <line x1="28" y1="8" x2="28" y2="48" />
        <line x1="12" y1="16" x2="44" y2="16" />
        <polygon points="6,34 18,34 12,20" />
        <polygon points="38,34 50,34 44,20" />
        <line x1="18" y1="48" x2="38" y2="48" />
      </g>
      <text x="825" y="491" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Low TTL: fast failover but more queries; high TTL: less load but delayed changes</text>
    </g>
  </g>

  <!-- ==================== MIDDLE PANELS ==================== -->

  <!-- Second Panel: Negative caching -->
  <g id="panel-negative-caching">
    <rect x="40" y="555" width="860" height="465" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

    <!-- Icon: Shield / DNS search icon (56px) -->
    <g transform="translate(65, 575)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="24" cy="24" r="16" />
      <line x1="36" y1="36" x2="48" y2="48" />
      <line x1="18" y1="18" x2="30" y2="30" />
      <line x1="30" y1="18" x2="18" y2="30" />
    </g>
    <!-- Panel Title (30px bold) -->
    <text x="135" y="612" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Negative caching</text>

    <!-- Card 1: NXDOMAIN -->
    <g id="card-nxdomain">
      <rect x="65" y="650" width="375" height="155" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Search miss icon (56px) -->
      <g transform="translate(85, 665)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="22" cy="22" r="14" />
        <line x1="32" y1="32" x2="44" y2="44" />
        <line x1="16" y1="16" x2="28" y2="28" />
        <line x1="28" y1="16" x2="16" y2="28" />
      </g>
      <text x="252" y="742" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#303a36">NXDOMAIN</text>
    </g>

    <!-- Card 2: you create the record -->
    <g id="card-create-record">
      <rect x="465" y="650" width="410" height="155" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Add record icon (56px) -->
      <g transform="translate(485, 665)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="6" width="36" height="44" rx="4" />
        <line x1="16" y1="18" x2="36" y2="18" />
        <line x1="26" y1="28" x2="26" y2="40" />
        <line x1="20" y1="34" x2="32" y2="34" />
      </g>
      <text x="670" y="740" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">you create the record</text>
    </g>

    <!-- Card 3: queries still fail for minutes -->
    <g id="card-queries-fail">
      <rect x="65" y="830" width="375" height="165" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- Error / Clock stall icon (56px) -->
      <g transform="translate(85, 845)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="20" />
        <polyline points="28,16 28,28 36,36" />
        <circle cx="44" cy="44" r="8" fill="#e8f1ea" stroke="#207448" />
        <line x1="41" y1="41" x2="47" y2="47" />
        <line x1="47" y1="41" x2="41" y2="47" />
      </g>
      <text x="252" y="910" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
        <tspan x="252" dy="0">queries still fail</tspan>
        <tspan x="252" dy="36">for minutes</tspan>
      </text>
    </g>

    <!-- Card 4: negative TTL 300 -->
    <g id="card-negative-ttl">
      <rect x="465" y="830" width="410" height="165" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <!-- SOA / Certificate authority badge icon (56px) -->
      <g transform="translate(485, 845)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="44" height="38" rx="4" />
        <line x1="6" y1="20" x2="50" y2="20" />
        <circle cx="16" cy="14" r="2.5" fill="#207448" />
        <circle cx="24" cy="14" r="2.5" fill="#207448" />
        <line x1="16" y1="32" x2="38" y2="32" />
      </g>
      <text x="670" y="928" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">negative TTL 300</text>
    </g>
  </g>

  <!-- Third Panel: SOA serial -->
  <g id="panel-soa-serial">
    <rect x="930" y="555" width="630" height="465" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

    <!-- Container Header Icon: Server replication / database sync icon (56px) -->
    <g transform="translate(955, 575)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="12" rx="20" ry="6" />
      <path d="M 8 12 v 14 c 0 3.3 9 6 20 6 s 20 -2.7 20 -6 v -14" />
      <path d="M 8 26 v 14 c 0 3.3 9 6 20 6 s 20 -2.7 20 -6 v -14" />
    </g>

    <!-- Inner Card holding SOA serial label -->
    <rect x="955" y="665" width="580" height="325" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Counter / Version update badge graphic (56px) -->
    <g transform="translate(1217, 700)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="42" rx="6" />
      <line x1="4" y1="20" x2="52" y2="20" />
      <line x1="28" y1="20" x2="28" y2="48" />
      <circle cx="16" cy="13" r="2.5" fill="#207448" />
      <circle cx="40" cy="13" r="2.5" fill="#207448" />
    </g>

    <!-- Label: SOA serial: increment it (YYYYMMDDnn, e.g. 2026102301) or secondaries never update -->
    <text x="1245" y="805" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">
      <tspan x="1245" dy="0">SOA serial: increment it</tspan>
      <tspan x="1245" dy="38" font-family="monospace" font-size="24">(YYYYMMDDnn, e.g. 2026102301) or</tspan>
      <tspan x="1245" dy="38">secondaries never update</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="bottom-takeaway-bar">
    <rect x="40" y="1045" width="1520" height="95" rx="14" fill="#207448" />
    <!-- Checkmark Icon (56px, white) -->
    <g transform="translate(65, 1065)" stroke="#ffffff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="18,28 25,35 38,20" />
    </g>
    <text x="820" y="1086" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
      <tspan x="820" dy="0">Before you call a record change finished, confirm that the SOA serial moved</tspan>
      <tspan x="820" dy="34">and that the secondaries picked it up</tspan>
    </text>
  </g>
</svg>"""

with open("test_ttl_candidate.svg", "w") as f:
    f.write(svg_template)

print("Wrote test_ttl_candidate.svg successfully!")
