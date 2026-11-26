import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

def generate_svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1050" width="1600" height="1050">
  <title>Histogram buckets: keep le, then take the quantile once</title>
  <desc>Visual explanation of Prometheus cumulative histogram buckets, showing why summing without le breaks histogram_quantile, why keeping le in the by clause succeeds, and the end-to-end pipeline from pod buckets to fleet p99.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="9" markerHeight="9" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#207448" />
    </marker>
    <pattern id="diag-stripes" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <line x1="0" y1="0" x2="0" y2="8" stroke="#207448" stroke-width="1.5" stroke-opacity="0.18" />
    </pattern>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1050" fill="#f5f8f5" />

  <!-- Title -->
  <text x="800" y="58" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Histogram buckets: keep le, </tspan>
    <tspan x="800" dy="56">then take the quantile once</tspan>
  </text>

  <!-- ==================== LEFT PANEL: Cumulative Histogram ==================== -->
  <g id="left-panel">
    <rect x="50" y="160" width="510" height="410" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Histogram Header Icon (56px) -->
    <g transform="translate(80, 185)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="6" y1="50" x2="50" y2="50" />
      <line x1="6" y1="6" x2="6" y2="50" />
      <rect x="12" y="32" width="7" height="18" fill="#e8f1ea" />
      <rect x="21" y="24" width="7" height="26" fill="#e8f1ea" />
      <rect x="30" y="14" width="7" height="36" fill="#e8f1ea" />
      <rect x="39" y="8" width="7" height="42" fill="#e8f1ea" />
    </g>

    <!-- Note on Left Panel -->
    <text x="315" y="205" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="315" dy="0">Each box counts every request</tspan>
      <tspan x="315" dy="34">at or under its bound: cumulative</tspan>
    </text>

    <!-- Cumulative Histogram Chart Area -->
    <!-- Base line -->
    <line x1="85" y1="520" x2="525" y2="520" stroke="#207448" stroke-width="2" stroke-linecap="round" />

    <!-- Box 1 -->
    <g transform="translate(95, 460)">
      <rect x="0" y="0" width="70" height="60" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <rect x="4" y="20" width="62" height="36" rx="3" fill="#207448" fill-opacity="0.12" />
    </g>

    <!-- Box 2 -->
    <g transform="translate(180, 420)">
      <rect x="0" y="0" width="70" height="100" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <rect x="4" y="20" width="62" height="76" rx="3" fill="#207448" fill-opacity="0.12" />
      <line x1="4" y1="60" x2="66" y2="60" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
    </g>

    <!-- Box 3 (Orange outline: where target quantile falls) -->
    <g transform="translate(265, 370)">
      <rect x="0" y="0" width="76" height="150" rx="6" fill="#ffffff" stroke="#db8129" stroke-width="4.5" />
      <rect x="5" y="20" width="66" height="125" rx="3" fill="#db8129" fill-opacity="0.15" />
      <line x1="5" y1="60" x2="71" y2="60" stroke="#db8129" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="5" y1="110" x2="71" y2="110" stroke="#db8129" stroke-width="1.5" stroke-dasharray="3 3" />
    </g>

    <!-- Box 4 -->
    <g transform="translate(356, 330)">
      <rect x="0" y="0" width="70" height="190" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <rect x="4" y="20" width="62" height="166" rx="3" fill="#207448" fill-opacity="0.12" />
      <line x1="4" y1="60" x2="66" y2="60" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="100" x2="66" y2="100" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="150" x2="66" y2="150" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
    </g>

    <!-- Box 5 (+Inf) -->
    <g transform="translate(441, 290)">
      <rect x="0" y="0" width="70" height="230" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <rect x="4" y="20" width="62" height="206" rx="3" fill="#207448" fill-opacity="0.12" />
      <line x1="4" y1="60" x2="66" y2="60" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="100" x2="66" y2="100" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="140" x2="66" y2="140" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
      <line x1="4" y1="180" x2="66" y2="180" stroke="#207448" stroke-width="1.5" stroke-dasharray="3 3" />
    </g>
  </g>

  <!-- ==================== MIDDLE: Interpolation Arrow ==================== -->
  <g id="middle-arrow-group">
    <!-- Bracket / pointer line from Box 3 up and right -->
    <path d="M 303 365 L 303 310 L 560 310" fill="none" stroke="#207448" stroke-width="3" stroke-dasharray="6 4" stroke-linejoin="round" />
    <circle cx="303" cy="365" r="5" fill="#db8129" />

    <!-- Main middle arrow spanning from Left to Right panel -->
    <line x1="560" y1="310" x2="880" y2="310" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

    <!-- Label above/below the arrow -->
    <text x="725" y="360" text-anchor="middle" fill="#303a36">
      <tspan x="725" dy="0" font-family="monospace" font-size="24">histogram_quantile</tspan>
      <tspan x="725" dy="32" font-family="sans-serif" font-size="24">interpolates inside</tspan>
      <tspan x="725" dy="32" font-family="sans-serif" font-size="24">the bucket that</tspan>
      <tspan x="725" dy="32" font-family="sans-serif" font-size="24">holds the quantile</tspan>
    </text>
  </g>

  <!-- ==================== RIGHT PANEL: Two-row Comparison ==================== -->
  <g id="right-panel">
    <rect x="890" y="160" width="660" height="410" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Row 1: Trap Card -->
    <g id="row1-trap">
      <rect x="915" y="185" width="610" height="170" rx="12" fill="#ffffff" stroke="#d9383a" stroke-width="2.5" />

      <!-- Red Cross Icon (48px) -->
      <g transform="translate(940, 210)" stroke="#d9383a" stroke-width="4.5" fill="none" stroke-linecap="round">
        <circle cx="24" cy="24" r="22" stroke-width="3.5" />
        <line x1="13" y1="13" x2="35" y2="35" />
        <line x1="35" y1="13" x2="13" y2="35" />
      </g>

      <!-- Row 1 Title -->
      <text x="1015" y="235" fill="#d9383a">
        <tspan x="1015" dy="0" font-family="sans-serif" font-size="30" font-weight="bold">Trap: </tspan>
        <tspan dy="0" font-family="monospace" font-size="30" font-weight="bold">sum by (model)</tspan>
        <tspan x="1015" dy="38" font-family="sans-serif" font-size="30" font-weight="bold">drops le</tspan>
      </text>

      <!-- Row 1 Note -->
      <text x="1015" y="325" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Breaks histogram_quantile</text>
    </g>

    <!-- Row 2: Right Card -->
    <g id="row2-right">
      <rect x="915" y="375" width="610" height="170" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

      <!-- Green Check Icon (48px) -->
      <g transform="translate(940, 400)" stroke="#207448" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="24" cy="24" r="22" stroke-width="3.5" />
        <path d="M 13 24 L 21 32 L 35 17" />
      </g>

      <!-- Row 2 Title -->
      <text x="1015" y="425" fill="#207448">
        <tspan x="1015" dy="0" font-family="sans-serif" font-size="30" font-weight="bold">Right: </tspan>
        <tspan dy="0" font-family="monospace" font-size="30" font-weight="bold">sum by (le, model)</tspan>
      </text>

      <!-- Row 2 Note -->
      <text x="1015" y="478" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1015" dy="0">Keep le in the by clause, </tspan>
        <tspan x="1015" dy="34">then take the quantile once</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== BOTTOM FLOW: End-to-End Pipeline ==================== -->
  <g id="bottom-flow">
    <rect x="50" y="620" width="1500" height="300" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Pod A buckets (Stage 1A) -->
    <g id="pod-a">
      <rect x="90" y="650" width="260" height="105" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <!-- Pod Icon (40px) -->
      <g transform="translate(112, 680)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="34" height="24" rx="4" />
        <line x1="3" y1="15" x2="37" y2="15" />
        <circle cx="10" cy="9" r="2" fill="#207448" />
        <circle cx="10" cy="21" r="2" fill="#207448" />
      </g>
      <text x="165" y="715" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Pod A buckets</text>
    </g>

    <!-- Pod B buckets (Stage 1B) -->
    <g id="pod-b">
      <rect x="90" y="785" width="260" height="105" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <!-- Pod Icon (40px) -->
      <g transform="translate(112, 815)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="34" height="24" rx="4" />
        <line x1="3" y1="15" x2="37" y2="15" />
        <circle cx="10" cy="15" r="2" fill="#207448" />
        <circle cx="10" cy="21" r="2" fill="#207448" />
      </g>
      <text x="165" y="850" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">Pod B buckets</text>
    </g>

    <!-- Arrows from Pod A & Pod B to rate per series -->
    <line x1="350" y1="702" x2="420" y2="702" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
    <line x1="350" y1="838" x2="420" y2="838" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

    <!-- rate per series (Stage 2) -->
    <g id="stage-rate">
      <rect x="430" y="650" width="300" height="240" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <!-- Rate / Gauge Icon (56px) -->
      <g transform="translate(552, 675)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="24" />
        <line x1="28" y1="28" x2="42" y2="16" />
        <circle cx="28" cy="28" r="4" fill="#207448" />
        <path d="M 12 36 A 20 20 0 0 1 44 36" stroke-dasharray="3 4" />
      </g>
      <text x="580" y="785" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="580" dy="0">rate</tspan>
        <tspan x="580" dy="38">per series</tspan>
      </text>
    </g>

    <!-- Arrow from Stage 2 to Stage 3 -->
    <line x1="730" y1="770" x2="800" y2="770" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

    <!-- sum by (le, model) (Stage 3) -->
    <g id="stage-sum">
      <rect x="810" y="650" width="310" height="240" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <!-- Sigma / Aggregation Icon (56px) -->
      <g transform="translate(937, 675)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="4" width="48" height="48" rx="8" />
        <path d="M 40 16 L 18 16 L 30 28 L 18 40 L 40 40" />
      </g>
      <text x="965" y="785" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">
        <tspan x="965" dy="0">sum by</tspan>
        <tspan x="965" dy="38">(le, model)</tspan>
      </text>
    </g>

    <!-- Arrow from Stage 3 to Stage 4 -->
    <line x1="1120" y1="770" x2="1190" y2="770" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

    <!-- histogram_quantile(0.99) (Stage 4) -->
    <g id="stage-quantile">
      <rect x="1200" y="650" width="310" height="240" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
      <!-- Target / Percentile Icon (56px) -->
      <g transform="translate(1327, 675)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="24" />
        <circle cx="28" cy="28" r="14" />
        <line x1="28" y1="4" x2="28" y2="10" />
        <line x1="28" y1="46" x2="28" y2="52" />
        <line x1="4" y1="28" x2="10" y2="28" />
        <line x1="46" y1="28" x2="52" y2="28" />
        <circle cx="28" cy="28" r="4" fill="#207448" />
      </g>
      <text x="1355" y="785" text-anchor="middle" font-family="monospace" font-size="25" font-weight="bold" fill="#303a36"><tspan x="1355" dy="0">histogram_quantile</tspan><tspan x="1355" dy="38">(0.99)</tspan></text>
    </g>
  </g>

  <!-- ==================== CAPTION ==================== -->
  <text x="800" y="985" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">le stands for less than or equal to.</text>

</svg>'''

if __name__ == '__main__':
    content = generate_svg()
    pathlib.Path('test_candidate_le.svg').write_text(content)
    print("Generated test_candidate_le.svg successfully.")
