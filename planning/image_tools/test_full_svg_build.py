import re
import xml.etree.ElementTree as ET

svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1060" viewBox="0 0 1600 1060">
  <title>Node lifecycle</title>
  <desc>State diagram showing Slurm node lifecycle states and transitions</desc>

  <defs>
    <marker id="arrow" viewBox="0 0 16 16" refX="14" refY="8" markerWidth="14" markerHeight="14" orient="auto-start-reverse">
      <path d="M 0 2 L 14 8 L 0 14 Z" fill="#207448"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="1600" height="1060" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Node lifecycle</text>

  <!-- ==================== TRANSITION LABELS (placed cleanly beside arrows) ==================== -->

  <!-- Label 2: job starts (above Arrow 2 at y=235) -->
  <rect x="705" y="180" width="190" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="800" y="212" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">job starts</text>

  <!-- Label 3: job ends (below Arrow 3 at y=285) -->
  <rect x="720" y="295" width="160" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="800" y="327" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">job ends</text>

  <!-- Label 5: scontrol resume (beside Arrow 5 at x=450) -->
  <rect x="520" y="382" width="270" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="655" y="414" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">scontrol resume</text>

  <!-- Shared trigger label: scontrol drain / health check -->
  <rect x="560" y="450" width="480" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="800" y="482" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">scontrol drain / health check</text>

  <!-- Label 7: running jobs finish (above Arrow 7 at y=560) -->
  <rect x="640" y="504" width="320" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="800" y="536" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">running jobs finish</text>

  <!-- Label 8: node failure (jobs requeued or failed) (above horizontal segment at y=730) -->
  <rect x="960" y="674" width="590" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="1255" y="706" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">node failure (jobs requeued or failed)</text>

  <!-- Label 10: resume or ReturnToService on valid registration (above horizontal segment at y=810) -->
  <rect x="135" y="754" width="720" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="495" y="786" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">resume or ReturnToService on valid registration</text>

  <!-- Label 9: slurmd not responding (SlurmdTimeout) / admin (above horizontal segment at y=1020) -->
  <rect x="145" y="964" width="690" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="490" y="996" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">slurmd not responding (SlurmdTimeout) / admin</text>

  <!-- ==================== ARROWS (Continuous orthogonal paths) ==================== -->

  <!-- 1. [*] -> IDLE -->
  <circle cx="95" cy="225" r="16" fill="#207448"/>
  <path d="M 111 225 L 230 225" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- 2. IDLE -> ALLOCATED (job starts) -->
  <path d="M 530 235 L 1070 235" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- 3. ALLOCATED -> IDLE (job ends) -->
  <path d="M 1070 285 L 530 285" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- 4. IDLE -> DRAINED (scontrol drain / health check) -->
  <path d="M 330 305 L 330 515" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- 5. DRAINED -> IDLE (scontrol resume) -->
  <path d="M 450 515 L 450 305" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- 6. ALLOCATED -> DRAINING (scontrol drain / health check) -->
  <path d="M 1220 305 L 1220 515" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- Connector dashes visually linking shared trigger to both drain arrows -->
  <line x1="330" y1="473" x2="560" y2="473" stroke="#207448" stroke-width="2" stroke-dasharray="6,4"/>
  <line x1="1040" y1="473" x2="1220" y2="473" stroke="#207448" stroke-width="2" stroke-dasharray="6,4"/>

  <!-- 7. DRAINING -> DRAINED (running jobs finish) -->
  <path d="M 1070 560 L 530 560" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- 8. ALLOCATED -> DOWN (node failure (jobs requeued or failed)) -->
  <path d="M 1370 260 L 1560 260 L 1560 730 L 980 730 L 980 900" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- 9. IDLE -> DOWN (slurmd not responding (SlurmdTimeout) / admin) -->
  <path d="M 230 290 L 60 290 L 60 1020 L 900 1020 L 900 990" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- 10. DOWN -> IDLE (resume or ReturnToService on valid registration) -->
  <path d="M 820 900 L 820 810 L 140 810 L 140 260 L 230 260" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>

  <!-- ==================== STATE NODES ==================== -->

  <!-- Node: IDLE -->
  <g id="node-idle">
    <rect x="230" y="215" width="300" height="90" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Icon: Server ready -->
    <rect x="248" y="233" width="48" height="48" rx="8" fill="none" stroke="#207448" stroke-width="3"/>
    <circle cx="262" cy="257" r="4" fill="#207448"/>
    <line x1="274" y1="257" x2="286" y2="257" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
    <text x="415" y="271" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">IDLE</text>
  </g>

  <!-- Node: ALLOCATED -->
  <g id="node-allocated">
    <rect x="1070" y="215" width="300" height="90" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Icon: CPU chip with core activity -->
    <rect x="1088" y="233" width="48" height="48" rx="8" fill="none" stroke="#207448" stroke-width="3"/>
    <rect x="1100" y="245" width="24" height="24" rx="4" fill="#207448"/>
    <text x="1255" y="271" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">ALLOCATED</text>
  </g>

  <!-- Node: DRAINED -->
  <g id="node-drained">
    <rect x="230" y="515" width="300" height="90" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Icon: Maintenance shield -->
    <path d="M 272 533 Q 296 540 296 553 Q 296 575 272 581 Q 248 575 248 553 Q 248 540 272 533 Z" fill="none" stroke="#207448" stroke-width="3"/>
    <line x1="272" y1="544" x2="272" y2="562" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
    <text x="415" y="571" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">DRAINED</text>
  </g>

  <!-- Node: DRAINING -->
  <g id="node-draining">
    <rect x="1070" y="515" width="300" height="90" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
    <!-- Icon: Draining hourglass -->
    <path d="M 1094 535 L 1130 535 L 1112 557 L 1130 580 L 1094 580 L 1112 557 Z" fill="none" stroke="#207448" stroke-width="3" stroke-linejoin="round"/>
    <text x="1255" y="571" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">DRAINING</text>
  </g>

  <!-- Node: DOWN (Orange highlight as the single most important failure state) -->
  <g id="node-down">
    <rect x="750" y="900" width="300" height="90" rx="14" fill="#e8f1ea" stroke="#db8129" stroke-width="4"/>
    <!-- Icon: Alert triangle -->
    <path d="M 792 917 L 816 959 L 768 959 Z" fill="none" stroke="#db8129" stroke-width="3" stroke-linejoin="round"/>
    <line x1="792" y1="932" x2="792" y2="945" stroke="#db8129" stroke-width="3" stroke-linecap="round"/>
    <circle cx="792" cy="952" r="2" fill="#db8129"/>
    <text x="935" y="956" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">DOWN</text>
  </g>
</svg>"""

with open("output_perfect.svg", "w") as f:
    f.write(svg)

print("Saved output_perfect.svg")
