svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1150" width="1600" height="1150">
  <title>Where each startup interval comes from</title>
  <desc>Horizontal pod startup timeline illustrating sources and metrics for intervals from creation to readiness, including kubelet pod start duration and SLI bracket overlays, alongside warm and cold node latency profiles.</desc>

  <defs>
    <!-- Arrowhead Green (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1150" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Where each startup interval comes from</text>

  <!-- ==================== TOP BRACKET OVERLAYS ==================== -->
  
  <!-- Bracket 1: kubelet_pod_start_duration_seconds -->
  <!-- Spans from Scheduled (x=305) to Container start (x=1305) -->
  <g id="bracket-total">
    <rect x="285" y="76" width="1035" height="80" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <path d="M 305 156 V 168 M 1295 156 V 168" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    <text x="802" y="108" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="802" dy="0" font-family="monospace">kubelet_pod_start_duration_seconds:</tspan>
      <tspan x="802" dy="30">from kubelet first seeing the pod until all regular containers run, includes image pull</tspan>
    </text>
  </g>

  <!-- Bracket 2: kubelet_pod_start_sli_duration_seconds -->
  <!-- Spans Sandbox and Container Start, excludes image pull and init container -->
  <g id="bracket-sli">
    <rect x="350" y="166" width="905" height="80" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" stroke-dasharray="6 4" />
    <path d="M 550 246 V 258 M 1060 246 V 258" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    <text x="802" y="198" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="802" dy="0" font-family="monospace" fill="#207448">kubelet_pod_start_sli_duration_seconds:</tspan>
      <tspan x="802" dy="30">SIG-Scalability SLI, excludes image pull and init container runtime</tspan>
    </text>
  </g>

  <!-- ==================== HORIZONTAL TIMELINE BAR ==================== -->
  <!-- 6 segments across width: x=50 to 1550 (width 1500, height 132) -->

  <!-- Segment 1: Created to Scheduled -->
  <g id="seg-created-scheduled">
    <rect x="50" y="258" width="245" height="132" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Clock / timer icon (centered above text) -->
    <g transform="translate(152, 270)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="20" cy="20" r="18" />
      <polyline points="20,10 20,20 28,20" />
    </g>
    <text x="172" y="338" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="172" dy="0">Created to</tspan>
      <tspan x="172" dy="33">Scheduled</tspan>
    </text>
  </g>

  <!-- Flow arrow 1 -> 2 -->
  <line x1="295" y1="324" x2="307" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 2: Scheduled to Initialized -->
  <g id="seg-scheduled-initialized">
    <rect x="310" y="258" width="250" height="132" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Disk / mount icon (centered above text) -->
    <g transform="translate(415, 270)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="20" cy="11" rx="18" ry="7" />
      <path d="M 2 11 V 33 C 2 37 10 40 20 40 C 30 40 38 37 38 33 V 11" />
      <path d="M 2 22 C 2 26 10 29 20 29 C 30 29 38 26 38 22" />
    </g>
    <text x="435" y="338" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="435" dy="0">Scheduled to</tspan>
      <tspan x="435" dy="33">Initialized</tspan>
    </text>
  </g>

  <!-- Flow arrow 2 -> 3 -->
  <line x1="560" y1="324" x2="572" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 3: Sandbox -->
  <g id="seg-sandbox">
    <rect x="575" y="258" width="230" height="132" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Network / sandbox container box icon (centered above text) -->
    <g transform="translate(670, 270)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="36" height="36" rx="6" />
      <circle cx="20" cy="20" r="7" />
      <line x1="2" y1="20" x2="13" y2="20" />
      <line x1="27" y1="20" x2="38" y2="20" />
      <line x1="20" y1="2" x2="20" y2="13" />
      <line x1="20" y1="27" x2="20" y2="38" />
    </g>
    <text x="690" y="352" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Sandbox</text>
  </g>

  <!-- Flow arrow 3 -> 4 -->
  <line x1="805" y1="324" x2="817" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 4: Pull (Orange: Primary Cold Start Delay) -->
  <g id="seg-pull">
    <rect x="820" y="258" width="235" height="132" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="3.5" />
    <!-- Image download / registry pull icon (centered above text) -->
    <g transform="translate(917, 270)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="38" height="24" rx="4" />
      <polyline points="14,18 21,25 28,18" />
      <line x1="21" y1="8" x2="21" y2="25" />
      <line x1="6" y1="36" x2="36" y2="36" />
    </g>
    <text x="937" y="352" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">Pull</text>
  </g>

  <!-- Flow arrow 4 -> 5 -->
  <line x1="1055" y1="324" x2="1067" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 5: Container start -->
  <g id="seg-container-start">
    <rect x="1070" y="258" width="245" height="132" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Application window / process start icon (centered above text) -->
    <g transform="translate(1172, 270)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="38" height="34" rx="5" />
      <line x1="2" y1="14" x2="40" y2="14" />
      <polygon points="15,21 27,27 15,33" fill="#207448" stroke="none" />
    </g>
    <text x="1192" y="338" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="1192" dy="0">Container</tspan>
      <tspan x="1192" dy="33">start</tspan>
    </text>
  </g>

  <!-- Flow arrow 5 -> 6 -->
  <line x1="1315" y1="324" x2="1327" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 6: Ready -->
  <g id="seg-ready">
    <rect x="1330" y="258" width="220" height="132" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Checkmark shield / ready probe icon (centered above text) -->
    <g transform="translate(1420, 270)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 20 4 L 36 10 V 22 C 36 32 28 38 20 41 C 12 38 4 32 4 22 V 10 Z" />
      <polyline points="12,22 17,27 28,15" />
    </g>
    <text x="1440" y="352" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Ready</text>
  </g>

  <!-- ==================== SOURCES UNDER EACH SEGMENT ==================== -->

  <!-- Left Column Group Connector -->
  <path d="M 430 390 V 418" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Right Column Group Connector -->
  <path d="M 1190 390 V 418" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Left Column Group: Sources 1, 2, 3 -->
  <!-- Card 1: Created to Scheduled Source -->
  <g id="card-src-1">
    <rect x="50" y="418" width="725" height="134" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(75, 456)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 38,28" />
    </g>
    <text x="430" y="475" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="430" dy="0"><tspan font-family="monospace">creationTimestamp</tspan> versus <tspan font-family="monospace">PodScheduled</tspan></tspan>
      <tspan x="430" dy="34"><tspan font-family="monospace">lastTransitionTime,</tspan> scheduler metrics</tspan>
    </text>
  </g>

  <!-- Card 2: Scheduled to Initialized Source -->
  <g id="card-src-2">
    <rect x="50" y="568" width="725" height="134" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(75, 606)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="20" ry="8" />
      <path d="M 8 14 V 42 C 8 46.4 17 50 28 50 C 39 50 48 46.4 48 42 V 14" />
      <path d="M 8 28 C 8 32.4 17 36 28 36 C 39 36 48 32.4 48 28" />
    </g>
    <text x="430" y="626" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="430" dy="0">init containers, volume mounts, sandbox;</tspan>
      <tspan x="430" dy="34"><tspan font-family="monospace">Initialized</tspan> condition</tspan>
    </text>
  </g>

  <!-- Card 3: Sandbox Source -->
  <g id="card-src-3">
    <rect x="50" y="718" width="725" height="134" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(75, 756)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="6" />
      <circle cx="28" cy="28" r="8" />
      <line x1="8" y1="28" x2="20" y2="28" />
      <line x1="36" y1="28" x2="48" y2="28" />
      <line x1="28" y1="8" x2="28" y2="20" />
      <line x1="28" y1="36" x2="28" y2="48" />
    </g>
    <text x="430" y="794" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">kubelet_run_podsandbox_duration_seconds</text>
  </g>

  <!-- Right Column Group: Sources 4, 5, 6 -->
  <!-- Card 4: Pull Source -->
  <g id="card-src-4">
    <rect x="825" y="418" width="725" height="134" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(850, 456)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="28" rx="4" />
      <polyline points="20,24 28,31 36,24" />
      <line x1="28" y1="12" x2="28" y2="31" />
      <line x1="12" y1="46" x2="44" y2="46" />
    </g>
    <text x="1205" y="462" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1205" dy="0">event Pulled in X,</tspan>
      <tspan x="1205" dy="32" font-family="monospace" font-weight="bold" fill="#207448">kubelet_image_pull_duration_seconds,</tspan>
      <tspan x="1205" dy="32">containerd logs</tspan>
    </text>
  </g>

  <!-- Card 5: Container start Source -->
  <g id="card-src-5">
    <rect x="825" y="568" width="725" height="134" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(850, 606)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="6" />
      <line x1="6" y1="20" x2="50" y2="20" />
      <polygon points="22,28 36,36 22,44" fill="#207448" stroke="none" />
    </g>
    <text x="1205" y="644" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan font-family="monospace">ContainersReady</tspan> time</text>
  </g>

  <!-- Card 6: Ready Source -->
  <g id="card-src-6">
    <rect x="825" y="718" width="725" height="134" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(850, 756)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 40 38 48 28 52 C 18 48 8 40 8 28 V 14 Z" />
      <polyline points="18,28 25,35 38,20" />
    </g>
    <text x="1205" y="794" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">readiness probe success, <tspan font-family="monospace">Ready</tspan> condition</text>
  </g>

  <!-- ==================== BOTTOM PANELS: WARM VS COLD NODE ==================== -->

  <!-- Left: Warm node numbers -->
  <g id="panel-warm-node">
    <rect x="50" y="872" width="725" height="236" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Fast cached disk icon -->
    <g transform="translate(80, 960)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <path d="M 28 14 L 34 24 L 46 26 L 36 34 L 40 46 L 28 38 L 16 46 L 20 34 L 10 26 L 22 24 Z" />
    </g>
    <text x="430" y="958" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="430" dy="0">API and scheduling tens of ms,</tspan>
      <tspan x="430" dy="38">sandbox and CNI 100 to 500 ms,</tspan>
      <tspan x="430" dy="38">container under 1 s</tspan>
    </text>
  </g>

  <!-- Right: Cold node numbers -->
  <g id="panel-cold-node">
    <rect x="825" y="872" width="725" height="236" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Cold cloud / network pull wait icon -->
    <g transform="translate(855, 960)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 16 40 C 10 40 6 35 6 30 C 6 25 10 21 15 21 C 16 14 22 8 30 8 C 39 8 46 15 46 24 C 49 24 52 27 52 31 C 52 36 48 40 42 40 Z" />
      <line x1="28" y1="28" x2="28" y2="46" />
      <polyline points="22,40 28,46 34,40" />
    </g>
    <text x="1205" y="958" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1205" dy="0">pull and unpack minutes,</tspan>
      <tspan x="1205" dy="38">PVC attach 5 to 60 s,</tspan>
      <tspan x="1205" dy="38">model load minutes</tspan>
    </text>
  </g>

</svg>'''

open("test_candidate.svg", "w").write(svg_code)
print("Updated test_candidate.svg successfully!")
