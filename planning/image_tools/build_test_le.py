import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1060" width="1600" height="1060">
  <title>Histogram buckets: keep le, then take the quantile once</title>
  <desc>Visual infographic explaining why Prometheus histogram queries must preserve the le label during aggregation before histogram_quantile interpolates inside the target bucket.</desc>

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
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Histogram buckets: keep le,</tspan>
    <tspan x="800" dy="54">then take the quantile once</tspan>
  </text>

  <!-- ==================== LEFT PANEL: CUMULATIVE HISTOGRAM ==================== -->
  <rect x="50" y="130" width="510" height="820" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Histogram Container Header Icon: Storage/Bar Chart -->
  <g transform="translate(80, 150)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="8" width="44" height="40" rx="4" />
    <line x1="16" y1="40" x2="16" y2="30" />
    <line x1="28" y1="40" x2="28" y2="20" />
    <line x1="40" y1="40" x2="40" y2="14" />
  </g>

  <!-- Baseline & Chart Area -->
  <g id="histogram-chart" transform="translate(80, 210)">
    <!-- Base card for the histogram chart -->
    <rect x="0" y="0" width="450" height="460" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" filter="url(#card-shadow)" />

    <!-- Y-axis guide line -->
    <line x1="45" y1="40" x2="45" y2="400" stroke="#d5dfd8" stroke-width="2" stroke-linecap="round" />
    <!-- X-axis baseline -->
    <line x1="45" y1="400" x2="425" y2="400" stroke="#207448" stroke-width="3" stroke-linecap="round" />

    <!-- Grid lines -->
    <line x1="45" y1="330" x2="420" y2="330" stroke="#e8f1ea" stroke-width="1.5" stroke-dasharray="4 4" />
    <line x1="45" y1="260" x2="420" y2="260" stroke="#e8f1ea" stroke-width="1.5" stroke-dasharray="4 4" />
    <line x1="45" y1="190" x2="420" y2="190" stroke="#e8f1ea" stroke-width="1.5" stroke-dasharray="4 4" />
    <line x1="45" y1="120" x2="420" y2="120" stroke="#e8f1ea" stroke-width="1.5" stroke-dasharray="4 4" />
    <line x1="45" y1="50" x2="420" y2="50" stroke="#e8f1ea" stroke-width="1.5" stroke-dasharray="4 4" />

    <!-- Row of 5 cumulative boxes rising from left to right -->
    <!-- Box 1 -->
    <rect x="65" y="330" width="58" height="70" rx="4" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <line x1="65" y1="365" x2="123" y2="365" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />

    <!-- Box 2 (cumulative: holds Box 1 + more) -->
    <rect x="137" y="260" width="58" height="140" rx="4" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <line x1="137" y1="330" x2="195" y2="330" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="137" y1="295" x2="195" y2="295" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />

    <!-- Box 3 (cumulative) -->
    <rect x="209" y="190" width="58" height="210" rx="4" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <line x1="209" y1="330" x2="267" y2="330" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="209" y1="260" x2="267" y2="260" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="209" y1="225" x2="267" y2="225" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />

    <!-- Box 4: Orange outline where target quantile falls (SINGLE ORANGE IN ENTIRE DIAGRAM) -->
    <rect x="281" y="120" width="58" height="280" rx="4" fill="#ffffff" stroke="#db8129" stroke-width="4.5" />
    <!-- Inner cumulative fill bands -->
    <rect x="285" y="124" width="50" height="272" rx="2" fill="#fff5eb" />
    <line x1="281" y1="330" x2="339" y2="330" stroke="#db8129" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="281" y1="260" x2="339" y2="260" stroke="#db8129" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="281" y1="190" x2="339" y2="190" stroke="#db8129" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="281" y1="155" x2="339" y2="155" stroke="#db8129" stroke-width="1.5" stroke-dasharray="2 2" />

    <!-- Box 5 (+Inf bucket, cumulative top) -->
    <rect x="353" y="50" width="58" height="350" rx="4" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <line x1="353" y1="330" x2="411" y2="330" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="353" y1="260" x2="411" y2="260" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="353" y1="190" x2="411" y2="190" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="353" y1="120" x2="411" y2="120" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />
    <line x1="353" y1="85" x2="411" y2="85" stroke="#207448" stroke-width="1.5" stroke-dasharray="2 2" />

    <!-- Small cumulative step riser stairs behind/above -->
    <path d="M 65 330 L 123 330 L 137 260 L 195 260 L 209 190 L 267 190 L 281 120 L 339 120 L 353 50 L 411 50" fill="none" stroke="#207448" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
  </g>

  <!-- Cumulative Note Card below Histogram -->
  <g transform="translate(80, 700)" filter="url(#card-shadow)">
    <rect x="0" y="0" width="450" height="220" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Info icon -->
    <g transform="translate(200, 24)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="25" cy="25" r="22" />
      <line x1="25" y1="22" x2="25" y2="35" stroke-width="4" />
      <circle cx="25" cy="14" r="2.5" fill="#207448" />
    </g>
    <!-- Exact Note Label -->
    <text x="225" y="115" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="225" dy="0">Each box counts every</tspan>
      <tspan x="225" dy="34">request at or under its</tspan>
      <tspan x="225" dy="34">bound: cumulative</tspan>
    </text>
  </g>


  <!-- ==================== MIDDLE: ARROW & LABEL ==================== -->
  <!-- Label above the arrow -->
  <text x="765" y="300" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="765" dy="0">histogram_quantile</tspan>
    <tspan x="765" dy="34">interpolates inside the bucket</tspan>
    <tspan x="765" dy="34">that holds the quantile</tspan>
  </text>

  <!-- Horizontal connecting arrow from left histogram to right panel -->
  <line x1="560" y1="420" x2="960" y2="420" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />


  <!-- ==================== RIGHT PANEL ==================== -->
  <rect x="970" y="130" width="580" height="820" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- ==================== ROW 1: TRAP ==================== -->
  <g transform="translate(995, 150)" filter="url(#card-shadow)">
    <rect x="0" y="0" width="530" height="110" rx="12" fill="#ffffff" stroke="#d9383a" stroke-width="2" />

    <!-- Red Cross Icon -->
    <g transform="translate(18, 30)" stroke="#d9383a" stroke-width="4.5" stroke-linecap="round">
      <circle cx="25" cy="25" r="22" fill="#fdf2f2" stroke="#d9383a" stroke-width="2" />
      <line x1="16" y1="16" x2="34" y2="34" />
      <line x1="34" y1="16" x2="16" y2="34" />
    </g>

    <!-- Trap Title -->
    <text x="80" y="44" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">
      <tspan x="80" dy="0">Trap: sum by (model) drops le</tspan>
    </text>

    <!-- Trap Note -->
    <text x="80" y="86" font-family="sans-serif" font-size="24" fill="#d9383a">
      <tspan x="80" dy="0">Breaks histogram_quantile</tspan>
    </text>
  </g>

  <!-- ==================== ROW 2: RIGHT ==================== -->
  <g transform="translate(995, 280)" filter="url(#card-shadow)">
    <rect x="0" y="0" width="530" height="135" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

    <!-- Green Check Icon -->
    <g transform="translate(18, 42)" stroke="#207448" stroke-width="4.5" stroke-linecap="round" stroke-linejoin="round" fill="none">
      <circle cx="25" cy="25" r="22" fill="#f0f7f2" stroke="#207448" stroke-width="2" />
      <polyline points="15,26 22,33 35,18" />
    </g>

    <!-- Right Title -->
    <text x="80" y="42" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">
      <tspan x="80" dy="0">Right: sum by (le, model)</tspan>
    </text>

    <!-- Right Note -->
    <text x="80" y="82" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="80" dy="0">Keep le in the by clause,</tspan>
      <tspan x="80" dy="32">then take the quantile once</tspan>
    </text>
  </g>

  <!-- ==================== FLOW CONTAINER BELOW THE ROWS ==================== -->
  <!-- Container for the 2 pods flow -->
  <rect x="995" y="440" width="530" height="485" rx="14" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />

  <!-- Node: Pod A buckets -->
  <g transform="translate(1015, 460)" filter="url(#card-shadow)">
    <rect x="0" y="0" width="235" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Pod / Container icon -->
    <g transform="translate(12, 12)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="38" height="36" rx="4" />
      <line x1="4" y1="18" x2="42" y2="18" />
      <circle cx="12" cy="12" r="2" fill="#207448" />
      <circle cx="20" cy="12" r="2" fill="#207448" />
    </g>
    <text x="68" y="46" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">Pod A buckets</text>
  </g>

  <!-- Node: Pod B buckets -->
  <g transform="translate(1270, 460)" filter="url(#card-shadow)">
    <rect x="0" y="0" width="235" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Pod / Container icon -->
    <g transform="translate(12, 12)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="38" height="36" rx="4" />
      <line x1="4" y1="18" x2="42" y2="18" />
      <circle cx="12" cy="12" r="2" fill="#207448" />
      <circle cx="20" cy="12" r="2" fill="#207448" />
    </g>
    <text x="68" y="46" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">Pod B buckets</text>
  </g>

  <!-- Arrows from Pod A and Pod B to rate per series -->
  <line x1="1132" y1="532" x2="1195" y2="575" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  <line x1="1388" y1="532" x2="1325" y2="575" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Node: rate per series -->
  <g transform="translate(1030, 580)" filter="url(#card-shadow)">
    <rect x="0" y="0" width="460" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Rate / Line chart icon -->
    <g transform="translate(16, 12)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="38" height="36" rx="4" />
      <polyline points="10,34 18,22 26,28 36,14" />
    </g>
    <text x="75" y="46" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">rate per series</text>
  </g>

  <!-- Arrow from rate per series to sum by (le, model) -->
  <line x1="1260" y1="652" x2="1260" y2="695" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Node: sum by (le, model) -->
  <g transform="translate(1030, 700)" filter="url(#card-shadow)">
    <rect x="0" y="0" width="460" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <!-- Sum / Sigma icon -->
    <g transform="translate(16, 12)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="38" height="36" rx="4" />
      <polyline points="32,16 16,16 25,24 16,32 32,32" />
    </g>
    <text x="75" y="46" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">sum by (le, model)</text>
  </g>

  <!-- Arrow from sum by (le, model) to histogram_quantile(0.99) -->
  <line x1="1260" y1="772" x2="1260" y2="815" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Node: histogram_quantile(0.99) -->
  <g transform="translate(1030, 820)" filter="url(#card-shadow)">
    <rect x="0" y="0" width="460" height="72" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Target / Quantile calculation icon -->
    <g transform="translate(16, 12)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="23" cy="24" r="16" />
      <circle cx="23" cy="24" r="7" />
      <line x1="23" y1="4" x2="23" y2="8" />
      <line x1="23" y1="40" x2="23" y2="44" />
      <line x1="3" y1="24" x2="7" y2="24" />
      <line x1="39" y1="24" x2="43" y2="24" />
    </g>
    <text x="75" y="46" font-family="monospace" font-size="25" font-weight="bold" fill="#207448">histogram_quantile(0.99)</text>
  </g>


  <!-- ==================== BOTTOM CAPTION / TAKEAWAY BAR ==================== -->
  <rect x="50" y="980" width="1500" height="56" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
  <text x="800" y="1017" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">le stands for less than or equal to.</text>

</svg>'''

with open("test_candidate_le.svg", "w") as f:
    f.write(svg_code)

print("Saved test_candidate_le.svg")
