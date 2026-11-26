#!/usr/bin/env python3

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Sizing the tail sampler and what happens at 8,000 traces per second</title>
  <desc>Sizing calculations for OpenTelemetry tail sampling comparing normal design point with traffic overload, listing remediations and symptom checks.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="56" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Sizing the tail sampler and what </tspan>
    <tspan x="800" dy="54">happens at 8,000 traces per second</tspan>
  </text>

  <!-- Formula Banner Box -->
  <rect x="40" y="145" width="1520" height="80" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <!-- Clock/Timer Icon -->
  <g transform="translate(68, 159)" stroke="#207448" stroke-width="4" fill="none">
    <circle cx="26" cy="26" r="22"/>
    <polyline points="26,13 26,26 38,26"/>
  </g>
  <text x="800" y="195" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">traces held = new traces per second x decision_wait</text>

  <!-- Left Column: Design point -->
  <rect x="40" y="265" width="740" height="425" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <!-- Gauge / Sliders Icon -->
  <g transform="translate(68, 281)" stroke="#207448" stroke-width="4" fill="none">
    <rect x="4" y="4" width="44" height="44" rx="8"/>
    <line x1="14" y1="12" x2="14" y2="40"/>
    <line x1="26" y1="12" x2="26" y2="40"/>
    <line x1="38" y1="12" x2="38" y2="40"/>
    <circle cx="14" cy="20" r="4" fill="#207448"/>
    <circle cx="26" cy="32" r="4" fill="#207448"/>
    <circle cx="38" cy="24" r="4" fill="#207448"/>
  </g>
  <text x="135" y="316" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#207448">Design point</text>

  <!-- Left Card 1 -->
  <rect x="60" y="350" width="700" height="96" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="80" y="388" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="80" dy="0">5,000 new traces per second x 30 s </tspan>
    <tspan x="80" dy="34">= 150,000 traces held</tspan>
  </text>

  <!-- Left Card 2 -->
  <rect x="60" y="460" width="700" height="62" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="80" y="499" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">num_traces set to 200,000 gives headroom</text>

  <!-- Left Card 3 -->
  <rect x="60" y="538" width="700" height="132" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="80" y="576" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="80" dy="0">with 20 spans of 1 KB each (assumptions, </tspan>
    <tspan x="80" dy="34">not measurements) = 3 GB of buffered span </tspan>
    <tspan x="80" dy="34">data before overhead</tspan>
  </text>

  <!-- Right Column: After a traffic increase (Single Orange focus) -->
  <rect x="820" y="265" width="740" height="425" rx="12" fill="#fff9f5" stroke="#db8129" stroke-width="3"/>
  <!-- Warning / Surge Triangle Icon -->
  <g transform="translate(848, 281)" stroke="#db8129" stroke-width="4" fill="none">
    <path d="M 26,6 L 48,44 L 4,44 Z" stroke-linejoin="round"/>
    <line x1="26" y1="19" x2="26" y2="30"/>
    <circle cx="26" cy="37" r="2" fill="#db8129"/>
  </g>
  <text x="915" y="316" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="#303a36">After a traffic increase</text>

  <!-- Right Big Failure Card -->
  <rect x="840" y="350" width="700" height="320" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="860" y="398" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="860" dy="0">8,000 per second x 30 s = 240,000 needed, </tspan>
    <tspan x="860" dy="38">which exceeds num_traces 200,000, so </tspan>
    <tspan x="860" dy="38">traces are dropped and the viewer </tspan>
    <tspan x="860" dy="38">shows fragments</tspan>
  </text>
  <!-- Visual fragment illustration inside card -->
  <g transform="translate(860, 580)" stroke="#303a36" stroke-width="2" fill="none">
    <rect x="0" y="0" width="120" height="36" rx="4" fill="#e8f1ea" stroke="#207448"/>
    <line x1="125" y1="18" x2="160" y2="18" stroke-dasharray="4,4"/>
    <rect x="165" y="0" width="70" height="36" rx="4" fill="#f5f8f5" stroke="#303a36" stroke-dasharray="3,3"/>
    <line x1="240" y1="18" x2="275" y2="18" stroke-dasharray="4,4"/>
    <rect x="280" y="0" width="110" height="36" rx="4" fill="#e8f1ea" stroke="#207448"/>
    <line x1="400" y1="8" x2="420" y2="28" stroke="#303a36" stroke-width="3"/>
    <line x1="420" y1="8" x2="400" y2="28" stroke="#303a36" stroke-width="3"/>
  </g>

  <!-- Bottom Left: Fix List Container -->
  <rect x="40" y="730" width="740" height="430" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <!-- Wrench / Tool Icon -->
  <g transform="translate(68, 747)" stroke="#207448" stroke-width="4" fill="none">
    <path d="M 12,38 L 26,24 M 22,20 C 19,17 19,11 23,7 C 27,3 33,3 36,6 L 30,12 L 35,17 L 41,11 C 44,14 44,20 40,24 C 36,28 30,28 27,25 Z"/>
  </g>

  <!-- Fix 1 -->
  <rect x="130" y="744" width="630" height="62" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="148" y="783" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">raise num_traces and memory together</text>

  <!-- Fix 2 -->
  <rect x="60" y="820" width="700" height="62" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="78" y="859" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">or reduce decision_wait</text>

  <!-- Fix 3 -->
  <rect x="60" y="896" width="700" height="62" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="78" y="935" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">add sampler replicas</text>

  <!-- Fix 4 -->
  <rect x="60" y="972" width="700" height="96" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="78" y="1010" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="78" dy="0">apply a head sample in tier one </tspan>
    <tspan x="78" dy="34">to cut the rate</tspan>
  </text>

  <!-- Fix 5 -->
  <rect x="60" y="1082" width="700" height="62" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="78" y="1121" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">alert on refusals</text>

  <!-- Bottom Right: Checklist Container -->
  <rect x="820" y="730" width="740" height="430" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <!-- Diagnostic / Search Icon -->
  <g transform="translate(848, 747)" stroke="#207448" stroke-width="4" fill="none">
    <circle cx="20" cy="20" r="14"/>
    <line x1="30" y1="30" x2="44" y2="44"/>
    <line x1="14" y1="20" x2="26" y2="20"/>
    <line x1="20" y1="14" x2="20" y2="26"/>
  </g>

  <!-- Check 1 -->
  <rect x="840" y="810" width="700" height="130" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="860" y="856" font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
    <tspan x="860" dy="0">otelcol_receiver_refused_spans non-zero </tspan>
    <tspan x="860" dy="38" font-family="system-ui, -apple-system, sans-serif">means the memory limiter is shedding load</tspan>
  </text>

  <!-- Check 2 -->
  <rect x="840" y="960" width="700" height="175" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="860" y="1006" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="860" dy="0">if the load balancing tier was scaled up, </tspan>
    <tspan x="860" dy="36">spans of one trace may be split across </tspan>
    <tspan x="860" dy="36">samplers while the routing pool changes</tspan>
  </text>
</svg>'''

with open("candidate_final.svg", "w") as f:
    f.write(svg_content)

print("candidate_final.svg generated successfully.")
