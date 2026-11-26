import re, subprocess, json

def build_svg():
    H = 1200
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">
  <title>A driver change goes out in batches: one canary host first, then growing batches, with a stop rule</title>
  <desc>Visual infographic explaining a progressive Ansible driver rollout: check run, canary batch with pre-task, sysctl, template, handler, and post-task validation, a stop rule on failure, followed by 10 percent and 100 percent batches and Slurm node resumption.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 1 3 L 16 9 L 1 15 Z" fill="#207448" />
    </marker>
    <marker id="arrow-red" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 1 3 L 16 9 L 1 15 Z" fill="#d93829" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="{H}" fill="#f5f8f5" />

  <!-- Title (48px bold, centered) -->
  <text x="800" y="74" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">A driver change goes out in batches:</tspan>
    <tspan x="800" dy="56">one canary host first, then growing batches,</tspan>
    <tspan x="800" dy="56">with a stop rule</tspan>
  </text>

  <!-- STAGE 1 BOX: x=40..280 (w=240, h=190, y=240) -->
  <g id="stage-1">
    <rect x="40" y="240" width="240" height="190" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <circle cx="76" cy="276" r="24" fill="#207448" />
    <text x="76" y="285" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <g transform="translate(208, 252)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="56" height="42" rx="6" />
      <path d="M 12 16 L 20 22 L 12 28" />
      <line x1="26" y1="28" x2="42" y2="28" />
    </g>
    <text x="160" y="335" text-anchor="middle" fill="#303a36">
      <tspan x="160" dy="0" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Check run:</tspan>
      <tspan x="160" dy="34" font-family="monospace" font-size="24">--check --diff</tspan>
      <tspan x="160" dy="32" font-family="monospace" font-size="24">--limit gpu001</tspan>
    </text>
  </g>

  <!-- Arrow: Stage 1 -> Stage 2 -->
  <path d="M 280 335 L 318 335" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- STAGE 2 BOX (Orange outline: #db8129): x=320..660 (w=340, h=190, y=240) -->
  <g id="stage-2">
    <rect x="320" y="240" width="340" height="190" rx="12" fill="#e8f1ea" stroke="#db8129" stroke-width="3.5" />
    <circle cx="356" cy="276" r="24" fill="#207448" />
    <text x="356" y="285" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <g transform="translate(588, 252)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="0" y="0" width="56" height="42" rx="6" />
      <circle cx="14" cy="21" r="4" fill="#207448" />
      <line x1="28" y1="14" x2="44" y2="14" />
      <line x1="28" y1="28" x2="44" y2="28" />
    </g>
    <text x="490" y="315" text-anchor="middle" fill="#303a36">
      <tspan x="490" dy="0" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">Canary batch of 1 host:</tspan>
      <tspan x="490" dy="30" font-family="sans-serif" font-size="24">pre-task checks the</tspan>
      <tspan x="490" dy="30" font-family="sans-serif" font-size="24">Slurm node shows</tspan>
      <tspan x="490" dy="30" font-family="sans-serif" font-size="24" font-weight="bold">DRAIN</tspan>
    </text>
  </g>

  <!-- Arrow: Stage 2 -> Stage 3 (Top horizontal progression) -->
  <path d="M 660 335 L 698 335" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Vertical flow inside Stage 2: Arrow Stage 2 -> Task 1 -->
  <path d="M 490 430 L 490 458" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- TASK 1: 'sysctl: persist vm.swappiness' (y=460, h=95) -->
  <g id="task-1">
    <rect x="320" y="460" width="340" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="490" y="500" text-anchor="middle" fill="#303a36">
      <tspan x="490" dy="0" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">sysctl: persist</tspan>
      <tspan x="490" dy="32" font-family="monospace" font-size="24">vm.swappiness</tspan>
    </text>
  </g>

  <!-- Arrow: Task 1 -> Task 2 -->
  <path d="M 490 555 L 490 583" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- TASK 2: 'template: override.conf' (y=585, h=95) -->
  <g id="task-2">
    <rect x="320" y="585" width="340" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="490" y="625" text-anchor="middle" fill="#303a36">
      <tspan x="490" dy="0" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">template:</tspan>
      <tspan x="490" dy="32" font-family="monospace" font-size="24">override.conf</tspan>
    </text>
  </g>

  <!-- Arrow: Task 2 -> Task 3 -->
  <path d="M 490 680 L 490 708" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- TASK 3: 'handler: restart nvidia-persistenced if changed' (y=710, h=125) -->
  <g id="task-3">
    <rect x="320" y="710" width="340" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="490" y="750" text-anchor="middle" fill="#303a36">
      <tspan x="490" dy="0" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">handler: restart</tspan>
      <tspan x="490" dy="30" font-family="monospace" font-size="24">nvidia-persistenced</tspan>
      <tspan x="490" dy="30" font-family="sans-serif" font-size="24">if changed</tspan>
    </text>
  </g>

  <!-- Arrow: Task 3 -> Task 4 -->
  <path d="M 490 835 L 490 863" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- TASK 4: 'post-task: nvidia-smi GPU count equals expected_gpus' (y=865, h=150) -->
  <g id="task-4">
    <rect x="320" y="865" width="340" height="150" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="490" y="903" text-anchor="middle" fill="#303a36">
      <tspan x="490" dy="0" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">post-task:</tspan>
      <tspan x="490" dy="28" font-family="monospace" font-size="24">nvidia-smi</tspan>
      <tspan x="490" dy="28" font-family="sans-serif" font-size="24">GPU count equals</tspan>
      <tspan x="490" dy="28" font-family="monospace" font-size="24">expected_gpus</tspan>
    </text>
  </g>

  <!-- RED DIAMOND (Validation stop rule between Stages 2 and 3) -->
  <!-- Left tip: x=685, Right tip: x=1135, Top tip: y=810, Bottom tip: y=1070, Center: (910, 940) -->
  <g id="red-diamond">
    <polygon points="910,810 1135,940 910,1070 685,940" fill="#fff5f5" stroke="#d93829" stroke-width="3.5" stroke-linejoin="round" />
    <g transform="translate(882, 825)" stroke="#d93829" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="28,4 52,18 52,38 28,52 4,38 4,18" fill="#d93829" />
      <line x1="18" y1="18" x2="38" y2="38" stroke="#ffffff" stroke-width="4" />
      <line x1="38" y1="18" x2="18" y2="38" stroke="#ffffff" stroke-width="4" />
    </g>
    <text x="910" y="915" text-anchor="middle" fill="#303a36">
      <tspan x="910" dy="0" font-family="sans-serif" font-size="24" font-weight="bold" fill="#d93829">validation fails:</tspan>
      <tspan x="910" dy="32" font-family="sans-serif" font-size="24">the play stops before</tspan>
      <tspan x="910" dy="30" font-family="sans-serif" font-size="24">the 10% batch</tspan>
    </text>
  </g>

  <!-- Arrow: Task 4 -> Red Diamond (Center of Task 4: y = 865 + 75 = 940!) -->
  <path d="M 660 940 L 683 940" fill="none" stroke="#d93829" stroke-width="3.5" marker-end="url(#arrow-red)" />

  <!-- STAGE 3 BOX: x=700..1020 (w=320, h=190, y=240) -->
  <g id="stage-3">
    <rect x="700" y="240" width="320" height="190" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <circle cx="736" cy="276" r="24" fill="#207448" />
    <text x="736" y="285" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <g transform="translate(948, 252)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <path d="M 28 4 L 28 28 L 50 16 Z" fill="#207448" fill-opacity="0.3" />
    </g>
    <text x="860" y="335" text-anchor="middle" fill="#303a36">
      <tspan x="860" dy="0" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">10% batch,</tspan>
      <tspan x="860" dy="34" font-family="monospace" font-size="24">max_fail_percentage</tspan>
      <tspan x="860" dy="30" font-family="monospace" font-size="24">5</tspan>
    </text>
  </g>

  <!-- Arrow: Stage 3 -> Stage 4 -->
  <path d="M 1020 335 L 1058 335" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- STAGE 4 BOX: x=1060..1270 (w=210, h=190, y=240) -->
  <g id="stage-4">
    <rect x="1060" y="240" width="210" height="190" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <circle cx="1096" cy="276" r="24" fill="#207448" />
    <text x="1096" y="285" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <g transform="translate(1198, 252)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <path d="M 28 4 A 24 24 0 1 1 27.9 4" fill="#207448" fill-opacity="0.3" />
    </g>
    <text x="1165" y="340" text-anchor="middle" fill="#303a36">
      <tspan x="1165" dy="0" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">remaining</tspan>
      <tspan x="1165" dy="34" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">100% batch</tspan>
    </text>
  </g>

  <!-- Arrow: Stage 4 -> Stage 5 -->
  <path d="M 1270 335 L 1308 335" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- STAGE 5 BOX: x=1310..1560 (w=250, h=200, y=240) -->
  <g id="stage-5">
    <rect x="1310" y="240" width="250" height="200" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="3.5" />
    <circle cx="1346" cy="276" r="24" fill="#207448" />
    <text x="1346" y="285" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>
    <g transform="translate(1488, 252)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <polyline points="18,28 26,36 40,18" />
    </g>
    <text x="1435" y="325" text-anchor="middle" fill="#303a36">
      <tspan x="1435" dy="0" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">Resume Slurm</tspan>
      <tspan x="1435" dy="28" font-family="sans-serif" font-size="24">nodes in a</tspan>
      <tspan x="1435" dy="28" font-family="sans-serif" font-size="24">separate,</tspan>
      <tspan x="1435" dy="28" font-family="sans-serif" font-size="24">explicit play</tspan>
    </text>
  </g>

  <!-- Takeaway bar at bottom -->
  <rect x="40" y="1090" width="1520" height="70" rx="12" fill="#207448" />
  <text x="800" y="1134" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Each stage catches a different kind of mistake.</text>
</svg>
'''
    return svg

open("test_candidate.svg", "w").write(build_svg())
