import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1060" width="1600" height="1060">
  <title>Histogram buckets: keep le, then take the quantile once</title>
  <desc>Visual explanation of Prometheus cumulative histogram buckets, showing why summing without le breaks histogram_quantile, why keeping le in the by clause succeeds, and the end-to-end pipeline from pod buckets to fleet p99.</desc>

  <defs>
    <!-- Green arrowhead (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>

    <!-- Card shadow -->
    <filter id="card-shadow" x="-4%" y="-4%" width="108%" height="108%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#207448" flood-opacity="0.08" />
    </filter>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1060" fill="#f5f8f5" />

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Histogram buckets: keep le,</tspan>
    <tspan x="800" dy="56">then take the quantile once</tspan>
  </text>

  <!-- ==================== LEFT PANEL: Cumulative Histogram ==================== -->
  <g id="left-panel">
    <rect x="50" y="150" width="520" height="440" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Histogram Header Icon (56px) -->
    <g transform="translate(75, 175)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="6" y1="50" x2="50" y2="50" />
      <line x1="6" y1="6" x2="6" y2="50" />
      <rect x="12" y="32" width="7" height="18" fill="#e8f1ea" />
      <rect x="21" y="24" width="7" height="26" fill="#e8f1ea" />
      <rect x="30" y="14" width="7" height="36" fill="#e8f1ea" />
      <rect x="39" y="8" width="7" height="42" fill="#e8f1ea" />
    </g>

    <!-- Note on Left Panel -->
    <text x="330" y="195" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="330" dy="0">Each box counts every</tspan>
      <tspan x="330" dy="32">request at or under its</tspan>
      <tspan x="330" dy="32">bound: cumulative</tspan>
    </text>

    <!-- Cumulative Histogram Chart Area -->
    <!-- Base line -->
    <line x1="80" y1="535" x2="540" y2="535" stroke="#207448" stroke-width="2.5" stroke-linecap="round" />

    <!-- Box 1 -->
    <g transform="translate(95, 475)">
      <rect x="0" y="0" width="70" height="60" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <rect x="4" y="16" width="62" height="40" rx="3" fill="#207448" fill-opacity="0.12" />
    </g>

    <!-- Box 2 -->
    <g transform="translate(180, 435)">
      <rect x="0" y="0" width="70" height="100" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <rect x="4" y="16" width="62" height="80" rx="3" fill="#207448" fill-opacity="0.12" />
      <line x1="4" y1="60" x2="66" y2="60" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
    </g>

    <!-- Box 3 (Orange outline: where target quantile falls - SINGLE ORANGE IN ENTIRE DIAGRAM) -->
    <g transform="translate(265, 385)">
      <rect x="0" y="0" width="76" height="150" rx="6" fill="#ffffff" stroke="#db8129" stroke-width="4.5" />
      <rect x="5" y="18" width="66" height="127" rx="3" fill="#fff5eb" />
      <line x1="5" y1="60" x2="71" y2="60" stroke="#db8129" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="5" y1="110" x2="71" y2="110" stroke="#db8129" stroke-width="1.5" stroke-dasharray="3 3" />
    </g>

    <!-- Box 4 -->
    <g transform="translate(356, 345)">
      <rect x="0" y="0" width="70" height="190" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <rect x="4" y="16" width="62" height="170" rx="3" fill="#207448" fill-opacity="0.12" />
      <line x1="4" y1="60" x2="66" y2="60" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="100" x2="66" y2="100" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="150" x2="66" y2="150" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
    </g>

    <!-- Box 5 (+Inf) -->
    <g transform="translate(441, 305)">
      <rect x="0" y="0" width="70" height="230" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <rect x="4" y="16" width="62" height="210" rx="3" fill="#207448" fill-opacity="0.12" />
      <line x1="4" y1="60" x2="66" y2="60" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="100" x2="66" y2="100" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="140" x2="66" y2="140" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="180" x2="66" y2="180" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
    </g>
  </g>

  <!-- ==================== MIDDLE: Interpolation Arrow ==================== -->
  <g id="middle-arrow-group">
    <!-- Main middle arrow spanning from Left to Right panel -->
    <line x1="570" y1="320" x2="880" y2="320" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

    <!-- Label above/below the arrow -->
    <text x="725" y="365" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="725" dy="0" font-family="monospace" font-size="24">histogram_quantile</tspan>
      <tspan x="725" dy="32">interpolates inside</tspan>
      <tspan x="725" dy="32">the bucket that</tspan>
      <tspan x="725" dy="32">holds the quantile</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT PANEL: Two-row Comparison ==================== -->
  <g id="right-panel">
    <rect x="890" y="150" width="660" height="440" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Row 1: Trap Card -->
    <g id="row1-trap">
      <rect x="915" y="175" width="610" height="185" rx="12" fill="#ffffff" stroke="#d9383a" stroke-width="2.5" filter="url(#card-shadow)" />

      <!-- Red Cross Icon (48px) -->
      <g transform="translate(940, 200)" stroke="#d9383a" stroke-width="4.5" fill="none" stroke-linecap="round">
        <circle cx="24" cy="24" r="22" stroke-width="3.5" />
        <line x1="13" y1="13" x2="35" y2="35" />
        <line x1="35" y1="13" x2="13" y2="35" />
      </g>

      <!-- Row 1 Title -->
      <text x="1015" y="222" font-family="sans-serif" font-size="30" font-weight="bold" fill="#d9383a">
        <tspan x="1015" dy="0">Trap: sum by (model)</tspan>
        <tspan x="1015" dy="38">drops le</tspan>
      </text>

      <!-- Row 1 Note -->
      <text x="1015" y="325" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Breaks histogram_quantile</text>
    </g>

    <!-- Row 2: Right Card -->
    <g id="row2-right">
      <rect x="915" y="380" width="610" height="185" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />

      <!-- Green Check Icon (48px) -->
      <g transform="translate(940, 405)" stroke="#207448" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="24" cy="24" r="22" stroke-width="3.5" />
        <path d="M 13 24 L 21 32 L 35 17" />
      </g>

      <!-- Row 2 Title -->
      <text x="1015" y="425" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Right: sum by (le, model)</text>

      <!-- Row 2 Note -->
      <text x="1015" y="480" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1015" dy="0">Keep le in the by clause,</tspan>
        <tspan x="1015" dy="34">then take the quantile once</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== BOTTOM FLOW: End-to-End Pipeline ==================== -->
  <g id="bottom-flow">
    <rect x="50" y="620" width="1500" height="320" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Pod A buckets (Stage 1A) -->
    <g id="pod-a">
      <rect x="75" y="650" width="240" height="115" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
      <!-- Pod Icon (40px) -->
      <g transform="translate(85, 688)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="34" height="24" rx="4" />
        <line x1="3" y1="15" x2="37" y2="15" />
        <circle cx="10" cy="9" r="2" fill="#207448" />
        <circle cx="10" cy="21" r="2" fill="#207448" />
      </g>
      <text x="210" y="698" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="210" dy="0">Pod A</tspan>
        <tspan x="210" dy="36">buckets</tspan>
      </text>
    </g>

    <!-- Pod B buckets (Stage 1B) -->
    <g id="pod-b">
      <rect x="75" y="795" width="240" height="115" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
      <!-- Pod Icon (40px) -->
      <g transform="translate(85, 833)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="34" height="24" rx="4" />
        <line x1="3" y1="15" x2="37" y2="15" />
        <circle cx="10" cy="15" r="2" fill="#207448" />
        <circle cx="10" cy="21" r="2" fill="#207448" />
      </g>
      <text x="210" y="843" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="210" dy="0">Pod B</tspan>
        <tspan x="210" dy="36">buckets</tspan>
      </text>
    </g>

    <!-- Arrows from Pod A & Pod B to rate per series -->
    <line x1="315" y1="707" x2="375" y2="707" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <line x1="315" y1="852" x2="375" y2="852" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- rate per series (Stage 2) -->
    <g id="stage-rate">
      <rect x="375" y="650" width="300" height="260" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
      <!-- Rate / Gauge Icon (56px) -->
      <g transform="translate(497, 685)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="24" />
        <line x1="28" y1="28" x2="42" y2="16" />
        <circle cx="28" cy="28" r="4" fill="#207448" />
        <path d="M 12 36 A 20 20 0 0 1 44 36" stroke-dasharray="3 4" />
      </g>
      <text x="525" y="785" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="525" dy="0">rate</tspan>
        <tspan x="525" dy="38">per series</tspan>
      </text>
    </g>

    <!-- Arrow from Stage 2 to Stage 3 -->
    <line x1="675" y1="780" x2="735" y2="780" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

    <!-- sum by (le, model) (Stage 3) -->
    <g id="stage-sum">
      <rect x="735" y="650" width="335" height="260" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
      <!-- Sigma / Aggregation Icon (56px) -->
      <g transform="translate(874, 700)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="48" height="48" rx="8" />
        <path d="M 40 16 L 18 16 L 30 28 L 18 40 L 40 40" />
      </g>
      <text x="902" y="805" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">sum by (le, model)</text>
    </g>

    <!-- Arrow from Stage 3 to Stage 4 -->
    <line x1="1070" y1="780" x2="1130" y2="780" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

    <!-- histogram_quantile(0.99) (Stage 4) -->
    <g id="stage-quantile">
      <rect x="1130" y="650" width="400" height="260" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" filter="url(#card-shadow)" />
      <!-- Target / Percentile Icon (56px) -->
      <g transform="translate(1302, 700)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="24" />
        <circle cx="28" cy="28" r="14" />
        <line x1="28" y1="4" x2="28" y2="10" />
        <line x1="28" y1="46" x2="28" y2="52" />
        <line x1="4" y1="28" x2="10" y2="28" />
        <line x1="46" y1="28" x2="52" y2="28" />
        <circle cx="28" cy="28" r="4" fill="#207448" />
      </g>
      <text x="1330" y="805" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">histogram_quantile(0.99)</text>
    </g>
  </g>

  <!-- ==================== CAPTION / TAKEAWAY BAR ==================== -->
  <rect x="50" y="975" width="1500" height="60" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <text x="800" y="1014" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">le stands for less than or equal to.</text>

</svg>'''

with open("test_candidate_refined.svg", "w") as f:
    f.write(svg_code)

print("Saved test_candidate_refined.svg")
