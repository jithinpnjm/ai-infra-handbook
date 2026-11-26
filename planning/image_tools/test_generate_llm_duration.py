import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1120" width="1600" height="1120">
  <title>RED for LLM serving: duration splits into four parts, each with its own fix</title>
  <desc>Horizontal timeline of an LLM request duration split into queue time, time to first token (TTFT), time per output token (TPOT), and total, with diagnostic pointers explaining what each part measures.</desc>

  <defs>
    <!-- Green Arrowhead (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1120" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">RED for LLM serving: duration splits into </tspan>
    <tspan x="800" dy="56">four parts, each with its own fix</tspan>
  </text>

  <!-- ==================== RED HEADER BANNER ==================== -->
  <g id="red-header">
    <rect x="360" y="140" width="880" height="64" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Signal / Meter Icon -->
    <g transform="translate(385, 147)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 42 A 22 22 0 0 1 44 42" />
      <line x1="25" y1="42" x2="38" y2="20" stroke="#207448" stroke-width="4" />
      <circle cx="25" cy="42" r="4" fill="#207448" />
    </g>
    <text x="825" y="183" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Request rate, Errors, Duration (percentiles)</text>
  </g>

  <!-- ==================== HORIZONTAL TIMELINE ==================== -->
  <!-- Timeline track background / flow line -->
  <line x1="40" y1="285" x2="1560" y2="285" stroke="#207448" stroke-width="3" stroke-dasharray="6 6" />

  <!-- Segment 1: queue time -->
  <g id="seg-queue">
    <rect x="40" y="245" width="356" height="80" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="218" y="294" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">queue time</text>
  </g>

  <!-- Segment 2: time to first token (TTFT) -->
  <g id="seg-ttft">
    <rect x="428" y="245" width="356" height="80" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="606" y="280" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="606" dy="0">time to first token </tspan>
      <tspan x="606" dy="28">(TTFT)</tspan>
    </text>
  </g>

  <!-- Segment 3: time per output token (TPOT) - repeated run of small segments -->
  <g id="seg-tpot">
    <rect x="816" y="245" width="356" height="80" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Visual small token run pills inside -->
    <rect x="828" y="253" width="56" height="12" rx="4" fill="#207448" opacity="0.3" />
    <rect x="892" y="253" width="56" height="12" rx="4" fill="#207448" opacity="0.4" />
    <rect x="956" y="253" width="56" height="12" rx="4" fill="#207448" opacity="0.5" />
    <rect x="1020" y="253" width="56" height="12" rx="4" fill="#207448" opacity="0.6" />
    <rect x="1084" y="253" width="76" height="12" rx="4" fill="#207448" opacity="0.7" />
    <text x="994" y="292" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="994" dy="0">time per output token </tspan>
      <tspan x="994" dy="28">(TPOT)</tspan>
    </text>
  </g>

  <!-- Segment 4: total -->
  <g id="seg-total">
    <rect x="1204" y="245" width="356" height="80" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <text x="1382" y="294" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">total</text>
  </g>

  <!-- ==================== POINTER ARROWS ==================== -->
  <!-- Pointer 1: queue time to Queue time card -->
  <line x1="218" y1="325" x2="218" y2="368" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Pointer 2: TTFT segment to TTFT card -->
  <line x1="606" y1="325" x2="606" y2="368" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Pointer 3: TPOT segment to TPOT card -->
  <line x1="994" y1="325" x2="994" y2="368" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Pointer 4: total segment to Total card -->
  <line x1="1382" y1="325" x2="1382" y2="368" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ==================== FOUR EXPLANATION CARDS ==================== -->

  <!-- Card 1: Queue time -->
  <g id="card-queue">
    <rect x="40" y="370" width="356" height="390" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Clock / Timer Icon -->
    <g transform="translate(190, 388)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <polyline points="28,14 28,28 40,28" />
    </g>
    <text x="218" y="482" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Queue time</text>
    <text x="218" y="534" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="218" dy="0">waiting before </tspan>
      <tspan x="218" dy="32">service starts: </tspan>
      <tspan x="218" dy="32">arrivals exceed </tspan>
      <tspan x="218" dy="32">capacity, or the </tspan>
      <tspan x="218" dy="32">batch scheduler </tspan>
      <tspan x="218" dy="32">holds batches for </tspan>
      <tspan x="218" dy="32">a fill timeout</tspan>
    </text>
  </g>

  <!-- Card 2: TTFT (Orange Outline) -->
  <g id="card-ttft">
    <rect x="428" y="370" width="356" height="390" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="3.5" />
    <!-- Compute / Chip Icon -->
    <g transform="translate(578, 388)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="4" />
      <path d="M 18 8 V 2 M 28 8 V 2 M 38 8 V 2" />
      <path d="M 18 54 V 48 M 28 54 V 48 M 38 54 V 48" />
      <path d="M 8 18 H 2 M 8 28 H 2 M 8 38 H 2" />
      <path d="M 54 18 H 48 M 54 28 H 48 M 54 38 H 48" />
    </g>
    <text x="606" y="482" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">TTFT</text>
    <text x="606" y="560" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="606" dy="0">prompt processing and </tspan>
      <tspan x="606" dy="36">everything before </tspan>
      <tspan x="606" dy="36">the first token</tspan>
    </text>
  </g>

  <!-- Card 3: TPOT -->
  <g id="card-tpot">
    <rect x="816" y="370" width="356" height="390" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Pulse / Speedometer / Token Step Icon -->
    <g transform="translate(966, 388)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <polyline points="12,32 22,18 34,36 44,24" />
    </g>
    <text x="994" y="482" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">TPOT</text>
    <text x="994" y="575" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="994" dy="0">steady generation </tspan>
      <tspan x="994" dy="36">speed per token</tspan>
    </text>
  </g>

  <!-- Card 4: Total -->
  <g id="card-total">
    <rect x="1204" y="370" width="356" height="390" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- User Feeling / Experience Icon (person with smile / heart) -->
    <g transform="translate(1354, 388)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="20" r="12" />
      <path d="M 10 50 C 10 38 18 34 28 34 C 38 34 46 38 46 50" />
    </g>
    <text x="1382" y="482" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Total</text>
    <text x="1382" y="590" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">what the user feels</text>
  </g>

  <!-- ==================== LOWER ROW: RULE BOX & SIDE LIST ==================== -->

  <!-- Rule Box (Left: 880px) -->
  <g id="rule-box">
    <rect x="40" y="795" width="880" height="175" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Balance / Scale Icon -->
    <g transform="translate(68, 852)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="10" y1="12" x2="46" y2="12" />
      <line x1="28" y1="12" x2="28" y2="46" />
      <line x1="16" y1="46" x2="40" y2="46" />
      <polyline points="10,12 4,28 16,28 10,12" />
      <polyline points="46,12 40,28 52,28 46,12" />
    </g>
    <text x="500" y="848" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="500" dy="0">The request rate shows at once whether a slowdown </tspan>
      <tspan x="500" dy="36">comes with more load (a load problem) or with the same </tspan>
      <tspan x="500" dy="36">load (architecture or resources)</tspan>
    </text>
  </g>

  <!-- Side List (Right: 608px) -->
  <g id="side-list">
    <rect x="952" y="795" width="608" height="175" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Checklist Icon -->
    <g transform="translate(980, 852)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="46" rx="4" />
      <line x1="14" y1="18" x2="22" y2="18" />
      <line x1="28" y1="18" x2="42" y2="18" />
      <line x1="14" y1="30" x2="22" y2="30" />
      <line x1="28" y1="30" x2="42" y2="30" />
      <line x1="14" y1="42" x2="22" y2="42" />
      <line x1="28" y1="42" x2="42" y2="42" />
    </g>
    <text x="1290" y="865" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1290" dy="0">Also track: tokens/s, batch size, </tspan>
      <tspan x="1290" dy="36">KV-cache utilisation, preemptions and </tspan>
      <tspan x="1290" dy="36">evictions</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1005" width="1520" height="70" rx="12" fill="#207448" />
    <text x="800" y="1048" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Each part points at a different fix, which is why the split repays the effort</text>
  </g>

</svg>"""

with open("test_output.svg", "w") as f:
    f.write(svg_content)

print("Saved test_output.svg")
