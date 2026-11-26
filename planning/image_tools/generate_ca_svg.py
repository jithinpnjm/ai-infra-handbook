import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Cluster Autoscaler: what triggers a node and what blocks its removal</title>
  <desc>Visual infographic explaining Kubernetes Cluster Autoscaler scale-up simulation and triggers versus scale-down threshold evaluation and eviction blocker conditions.</desc>

  <defs>
    <!-- Arrowhead Green (18px proportional) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Canvas Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Diagram Title (48px bold) -->
  <text x="800" y="62" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Cluster Autoscaler: what triggers a node and what blocks its removal</text>

  <!-- ========================================================================= -->
  <!-- LANE 1: Scale-up lane (x: 40 to 780, width: 740, y: 108 to 920, height: 812) -->
  <!-- ========================================================================= -->
  <g id="lane-scale-up">
    <!-- Lane Container -->
    <rect x="40" y="108" width="740" height="812" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Lane Header Icon: Scale-up Nodes Growth (56x56 outline, stroke 4, #207448) -->
    <g transform="translate(68, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="24" width="22" height="26" rx="4" />
      <rect x="34" y="8" width="22" height="42" rx="4" />
      <polyline points="12,16 17,10 22,16" />
      <line x1="17" y1="10" x2="17" y2="22" />
      <polyline points="40,4 45,-2 50,4" />
    </g>

    <!-- Lane Header Title (30px bold) -->
    <text x="142" y="154" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Scale-up lane</text>

    <!-- Step 1 Card: 1 pods Pending with FailedScheduling for insufficient resources -->
    <g id="scale-up-step-1">
      <rect x="65" y="178" width="690" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Number circle 1 (r=24, green, white number) -->
      <circle cx="102" cy="238" r="24" fill="#207448" />
      <text x="102" y="247" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
      <!-- Pending Pod Clock Icon (48x48 outline, stroke 3.5, #207448) -->
      <g transform="translate(144, 214)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="24" cy="24" r="19" />
        <polyline points="24,12 24,24 33,24" />
        <line x1="24" y1="2" x2="24" y2="5" />
      </g>
      <!-- Step 1 Text -->
      <text x="212" y="218" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="212" dy="0" font-weight="bold">1 pods Pending with </tspan><tspan x="212" dy="28">FailedScheduling for </tspan><tspan x="212" dy="28">insufficient resources</tspan></text>
    </g>

    <!-- Arrow 1 to 2 (Downwards) -->
    <line x1="410" y1="298" x2="410" y2="320" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Step 2 Card: 2 for each node group, simulate adding a node from its template: would the pod fit -->
    <g id="scale-up-step-2">
      <rect x="65" y="320" width="690" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Number circle 2 -->
      <circle cx="102" cy="380" r="24" fill="#207448" />
      <text x="102" y="389" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
      <!-- Template Simulation Blueprint Icon (48x48 outline, stroke 3.5, #207448) -->
      <g transform="translate(144, 356)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="6" width="36" height="36" rx="5" stroke-dasharray="5 3" />
        <path d="M 16 24 L 22 30 L 32 18" />
      </g>
      <!-- Step 2 Text -->
      <text x="212" y="358" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="212" dy="0" font-weight="bold">2 for each node group, simulate </tspan><tspan x="212" dy="28">adding a node from its template: </tspan><tspan x="212" dy="28">would the pod fit</tspan></text>
    </g>

    <!-- Arrow 2 to 3 (Downwards) -->
    <line x1="410" y1="440" x2="410" y2="462" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Step 3 Card: 3 expander picks among groups: random picks any, least-waste leaves the fewest empty seats, most-pods carries the most waiting pods -->
    <g id="scale-up-step-3">
      <rect x="65" y="462" width="690" height="174" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Number circle 3 -->
      <circle cx="102" cy="549" r="24" fill="#207448" />
      <text x="102" y="558" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
      <!-- Expander Selector / Decision Scales Icon (48x48 outline, stroke 3.5, #207448) -->
      <g transform="translate(144, 525)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <line x1="24" y1="8" x2="24" y2="40" />
        <line x1="8" y1="16" x2="40" y2="16" />
        <polygon points="8,16 3,30 13,30" />
        <polygon points="40,16 35,30 45,30" />
        <line x1="14" y1="40" x2="34" y2="40" />
      </g>
      <!-- Step 3 Text -->
      <text x="212" y="496" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="212" dy="0" font-weight="bold">3 expander picks among groups: </tspan><tspan x="212" dy="28">random picks any, least-waste </tspan><tspan x="212" dy="28">leaves the fewest empty seats, </tspan><tspan x="212" dy="28">most-pods carries the most waiting </tspan><tspan x="212" dy="28">pods</tspan></text>
    </g>

    <!-- Arrow 3 to 4 (Downwards) -->
    <line x1="410" y1="636" x2="410" y2="658" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Step 4 Card: 4 group size raised within its min and max -->
    <g id="scale-up-step-4">
      <rect x="65" y="658" width="690" height="124" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Number circle 4 -->
      <circle cx="102" cy="700" r="24" fill="#207448" />
      <text x="102" y="709" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
      <!-- Group Size Slider / Bounds Icon (48x48 outline, stroke 3.5, #207448) -->
      <g transform="translate(144, 676)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <line x1="6" y1="24" x2="42" y2="24" />
        <line x1="6" y1="14" x2="6" y2="34" />
        <line x1="42" y1="14" x2="42" y2="34" />
        <circle cx="24" cy="24" r="7" fill="#e8f1ea" />
      </g>
      <!-- Step 4 Text (Third line spans full width under icon for safety) -->
      <text x="212" y="694" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="212" dy="0" font-weight="bold">4 group size raised within its min </tspan><tspan x="212" dy="28">and max, for example </tspan><tspan x="95" dy="32" font-family="monospace">--nodes=1:10:worker-auto-scaling-group</tspan></text>
    </g>

    <!-- Arrow 4 to 5 (Downwards) -->
    <line x1="410" y1="782" x2="410" y2="804" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

    <!-- Step 5 Card: 5 node joins, scheduler places pods -->
    <g id="scale-up-step-5">
      <rect x="65" y="804" width="690" height="96" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Number circle 5 -->
      <circle cx="102" cy="852" r="24" fill="#207448" />
      <text x="102" y="861" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>
      <!-- Node Joined / Pod Placed Icon (48x48 outline, stroke 3.5, #207448) -->
      <g transform="translate(144, 828)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="10" width="36" height="30" rx="4" />
        <circle cx="15" cy="20" r="2.5" fill="#207448" />
        <polyline points="24,23 29,28 38,18" />
      </g>
      <!-- Step 5 Text -->
      <text x="212" y="846" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="212" dy="0" font-weight="bold">5 node joins, scheduler places </tspan><tspan x="212" dy="28">pods</tspan></text>
    </g>
  </g>

  <!-- ========================================================================= -->
  <!-- LANE 2: Scale-down lane (x: 820 to 1560, width: 740, y: 108 to 920, height: 812) -->
  <!-- ========================================================================= -->
  <g id="lane-scale-down">
    <!-- Lane Container -->
    <rect x="820" y="108" width="740" height="812" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Lane Header Icon: Scale-down Drain Nodes (56x56 outline, stroke 4, #207448) -->
    <g transform="translate(848, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="22" height="40" rx="4" />
      <rect x="34" y="26" width="22" height="24" rx="4" />
      <polyline points="40,16 45,22 50,16" />
      <line x1="45" y1="10" x2="45" y2="22" />
    </g>

    <!-- Lane Header Title (30px bold) -->
    <text x="922" y="154" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Scale-down lane</text>

    <!-- Scale-down Trigger Condition Card -->
    <g id="scale-down-condition-box">
      <rect x="845" y="178" width="690" height="178" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
      <!-- Gauge / Timer Outline Icon (56x56 outline, stroke 4, #207448) -->
      <g transform="translate(866, 198)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 12 38 A 20 20 0 1 1 44 38" />
        <line x1="28" y1="28" x2="18" y2="18" />
        <circle cx="28" cy="28" r="3" fill="#207448" />
        <line x1="8" y1="46" x2="48" y2="46" />
      </g>
      <!-- Condition Text (Monospace for flags and thresholds) -->
      <text x="936" y="214" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="936" dy="0">node utilisation (requests against </tspan><tspan x="936" dy="28">allocatable) below </tspan><tspan x="936" dy="28" font-family="monospace">--scale-down-utilization-threshold 0.5 </tspan><tspan x="936" dy="28">for </tspan><tspan font-family="monospace">--scale-down-unneeded-time 10 min, </tspan><tspan x="936" dy="28">then drain and remove</tspan></text>
    </g>

    <!-- Blockers Section (Sub-container inside Scale-down lane) -->
    <g id="blockers-container">
      <rect x="845" y="374" width="690" height="526" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

      <!-- Blockers Section Header Icon: Shield Protection (48x48 outline, stroke 3.5, #207448) -->
      <g transform="translate(866, 386)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 24 6 L 42 14 V 28 C 42 38 24 45 24 45 C 24 45 6 38 6 28 V 14 Z" />
        <line x1="16" y1="25" x2="32" y2="25" />
      </g>

      <!-- Blockers Header Title (30px bold) -->
      <text x="926" y="420" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Blockers list</text>

      <!-- Blocker 1: pods without controllers -->
      <g id="blocker-1">
        <rect x="862" y="434" width="656" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
        <!-- Unmanaged Pod Icon (36x36 outline, stroke 3, #207448) -->
        <g transform="translate(876, 445)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="18" cy="18" r="13" />
          <line x1="18" y1="10" x2="18" y2="26" />
          <line x1="10" y1="18" x2="26" y2="18" />
        </g>
        <text x="926" y="470" font-family="sans-serif" font-size="24" fill="#303a36">pods without controllers</text>
      </g>

      <!-- Blocker 2: emptyDir local storage unless annotated -->
      <g id="blocker-2">
        <rect x="862" y="498" width="656" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
        <!-- Disk Storage Cylinder Icon (36x36 outline, stroke 3, #207448) -->
        <g transform="translate(876, 509)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <ellipse cx="18" cy="10" rx="12" ry="5" />
          <path d="M 6 10 v 16 c 0 3 5 5 12 5 s 12 -2 12 -5 v -16" />
          <path d="M 6 18 c 0 3 5 5 12 5 s 12 -2 12 -5" />
        </g>
        <text x="926" y="534" font-family="sans-serif" font-size="24" fill="#303a36">emptyDir local storage unless annotated</text>
      </g>

      <!-- Blocker 3: PDBs -->
      <g id="blocker-3">
        <rect x="862" y="562" width="656" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
        <!-- Umbrella / Guardrail Icon (36x36 outline, stroke 3, #207448) -->
        <g transform="translate(876, 573)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M 6 22 a 12 12 0 0 1 24 0 Z" />
          <line x1="18" y1="22" x2="18" y2="30" />
          <path d="M 18 30 a 3 3 0 0 1 -6 0" />
        </g>
        <text x="926" y="598" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">PDBs</text>
      </g>

      <!-- Blocker 4: kube-system pods -->
      <g id="blocker-4">
        <rect x="862" y="626" width="656" height="58" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
        <!-- System Component Gear Icon (36x36 outline, stroke 3, #207448) -->
        <g transform="translate(876, 637)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="18" cy="18" r="6" />
          <path d="M 18 4 v 4 M 18 28 v 4 M 4 18 h 4 M 28 18 h 4 M 8 8 l 3 3 M 25 25 l 3 3 M 8 28 l 3 -3 M 25 11 l 3 -3" />
        </g>
        <text x="926" y="662" font-family="sans-serif" font-size="24" fill="#303a36">kube-system pods</text>
      </g>

      <!-- Blocker 5: annotation cluster-autoscaler.kubernetes.io/safe-to-evict false (SINGLE ORANGE ITEM) -->
      <g id="blocker-5-orange">
        <rect x="862" y="690" width="656" height="114" rx="8" fill="#fff9f2" stroke="#db8129" stroke-width="2.5" />
        <!-- Padlock Override Icon (36x36 outline, stroke 3, #db8129) -->
        <g transform="translate(876, 726)" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <rect x="6" y="14" width="24" height="18" rx="3" />
          <path d="M 11 14 V 9 C 11 5 25 5 25 9 V 14" />
          <circle cx="18" cy="23" r="2" fill="#db8129" />
        </g>
        <text x="926" y="726" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="926" dy="0">annotation </tspan><tspan x="926" dy="28" font-family="monospace">cluster-autoscaler.kubernetes.io/</tspan><tspan x="926" dy="28" font-family="monospace" fill="#db8129">safe-to-evict false</tspan></text>
      </g>

      <!-- Blocker 6: recently added node (scale-down-delay-after-add) -->
      <g id="blocker-6">
        <rect x="862" y="810" width="656" height="86" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
        <!-- Delay Timer / History Clock Icon (36x36 outline, stroke 3, #207448) -->
        <g transform="translate(876, 835)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="18" cy="18" r="14" />
          <polyline points="18,10 18,18 24,18" />
        </g>
        <text x="926" y="846" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="926" dy="0">recently added node </tspan><tspan x="926" dy="28" font-family="monospace">(scale-down-delay-after-add)</tspan></text>
      </g>
    </g>
  </g>

  <!-- ========================================================================= -->
  <!-- BOTTOM PANELS: Limits (Left) and GPU settings (Right)                     -->
  <!-- ========================================================================= -->

  <!-- Bottom Left Panel: Limits (x: 40 to 780, width: 740, y: 960 to 1160, height: 200) -->
  <g id="panel-limits">
    <rect x="40" y="960" width="740" height="200" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Limits Header Icon: Caution Octagon / Boundary (48x48 outline, stroke 3.5, #207448) -->
    <g transform="translate(68, 974)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="16,4 32,4 44,16 44,32 32,44 16,44 4,32 4,16" />
      <line x1="24" y1="14" x2="24" y2="26" />
      <circle cx="24" cy="33" r="1.5" fill="#207448" />
    </g>

    <!-- Limits Header Title (30px bold) -->
    <text x="134" y="1008" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Limits</text>

    <!-- Limits Card -->
    <g id="limits-card">
      <rect x="65" y="1030" width="690" height="114" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
      <text x="95" y="1066" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="95" dy="0">reacts only to Pending pods; assumes </tspan><tspan x="95" dy="28">homogeneous node groups; does not </tspan><tspan x="95" dy="28">understand gang all-or-nothing needs</tspan></text>
    </g>
  </g>

  <!-- Bottom Right Panel: GPU settings (x: 820 to 1560, width: 740, y: 960 to 1160, height: 200) -->
  <g id="panel-gpu-settings">
    <rect x="820" y="960" width="740" height="200" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- GPU Settings Header Icon: GPU Processor Chip (48x48 outline, stroke 3.5, #207448) -->
    <g transform="translate(848, 974)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="28" height="28" rx="4" />
      <rect x="16" y="16" width="16" height="16" rx="2" fill="#207448" fill-opacity="0.1" />
      <line x1="16" y1="4" x2="16" y2="10" />
      <line x1="24" y1="4" x2="24" y2="10" />
      <line x1="32" y1="4" x2="32" y2="10" />
      <line x1="16" y1="38" x2="16" y2="44" />
      <line x1="24" y1="38" x2="24" y2="44" />
      <line x1="32" y1="38" x2="32" y2="44" />
      <line x1="4" y1="16" x2="10" y2="16" />
      <line x1="4" y1="24" x2="10" y2="24" />
      <line x1="4" y1="32" x2="10" y2="32" />
      <line x1="38" y1="16" x2="44" y2="16" />
      <line x1="38" y1="24" x2="44" y2="24" />
      <line x1="38" y1="32" x2="44" y2="32" />
    </g>

    <!-- GPU Settings Header Title (30px bold) -->
    <text x="914" y="1008" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">GPU settings</text>

    <!-- GPU Settings Card -->
    <g id="gpu-card">
      <rect x="845" y="1030" width="690" height="114" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
      <text x="875" y="1076" font-family="monospace" font-size="24" fill="#303a36"><tspan x="875" dy="0">--gpu-total, burst pools min 0, </tspan><tspan x="875" dy="32">--balance-similar-node-groups</tspan></text>
    </g>
  </g>

</svg>'''

with open("candidate_ca.svg", "w") as f:
    f.write(svg_content)

print("candidate_ca.svg regenerated.")
