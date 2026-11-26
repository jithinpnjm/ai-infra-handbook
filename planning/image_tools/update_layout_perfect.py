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
  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Where each startup interval comes from</text>

  <!-- ==================== TOP BRACKET OVERLAYS ==================== -->
  
  <!-- Bracket 1: kubelet_pod_start_duration_seconds -->
  <!-- Spans from Scheduled (x=305) to Container start (x=1305) -->
  <g id="bracket-total">
    <rect x="290" y="80" width="1030" height="82" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <path d="M 310 162 V 176 M 1300 162 V 176" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    <text x="805" y="114" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="805" dy="0" font-family="monospace">kubelet_pod_start_duration_seconds:</tspan>
      <tspan x="805" dy="30">from kubelet first seeing the pod until all regular containers run, includes image pull</tspan>
    </text>
  </g>

  <!-- Bracket 2: kubelet_pod_start_sli_duration_seconds -->
  <!-- Spans Sandbox and Container Start, excludes image pull and init container -->
  <g id="bracket-sli">
    <rect x="350" y="176" width="910" height="82" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" stroke-dasharray="6 4" />
    <path d="M 550 258 V 270 M 1060 258 V 270" stroke="#207448" stroke-width="3" stroke-linecap="round" />
    <text x="805" y="210" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="805" dy="0" font-family="monospace" fill="#207448">kubelet_pod_start_sli_duration_seconds:</tspan>
      <tspan x="805" dy="30">SIG-Scalability SLI, excludes image pull and init container runtime</tspan>
    </text>
  </g>

  <!-- ==================== HORIZONTAL TIMELINE BAR ==================== -->
  <!-- 6 segments across width: x=50 to 1550 (width 1500, height 108) -->

  <!-- Segment 1: Created to Scheduled -->
  <g id="seg-created-scheduled">
    <rect x="50" y="270" width="245" height="108" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Clock / timer icon -->
    <g transform="translate(60, 296)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 38,28" />
    </g>
    <text x="180" y="322" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="180" dy="0">Created to</tspan>
      <tspan x="180" dy="34">Scheduled</tspan>
    </text>
  </g>

  <!-- Flow arrow 1 -> 2 -->
  <line x1="295" y1="324" x2="307" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 2: Scheduled to Initialized -->
  <g id="seg-scheduled-initialized">
    <rect x="310" y="270" width="245" height="108" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Disk / mount icon -->
    <g transform="translate(320, 296)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="20" ry="8" />
      <path d="M 8 14 V 42 C 8 46.4 17 50 28 50 C 39 50 48 46.4 48 42 V 14" />
      <path d="M 8 28 C 8 32.4 17 36 28 36 C 39 36 48 32.4 48 28" />
    </g>
    <text x="440" y="322" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="440" dy="0">Scheduled to</tspan>
      <tspan x="440" dy="34">Initialized</tspan>
    </text>
  </g>

  <!-- Flow arrow 2 -> 3 -->
  <line x1="555" y1="324" x2="567" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 3: Sandbox -->
  <g id="seg-sandbox">
    <rect x="570" y="270" width="235" height="108" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Network / sandbox container box icon -->
    <g transform="translate(582, 296)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="6" />
      <circle cx="28" cy="28" r="8" />
      <line x1="8" y1="28" x2="20" y2="28" />
      <line x1="36" y1="28" x2="48" y2="28" />
      <line x1="28" y1="8" x2="28" y2="20" />
      <line x1="28" y1="36" x2="28" y2="48" />
    </g>
    <text x="700" y="333" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Sandbox</text>
  </g>

  <!-- Flow arrow 3 -> 4 -->
  <line x1="805" y1="324" x2="817" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 4: Pull (Orange: Primary Cold Start Delay) -->
  <g id="seg-pull">
    <rect x="820" y="270" width="235" height="108" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="3.5" />
    <!-- Image download / registry pull icon -->
    <g transform="translate(835, 296)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="28" rx="4" />
      <polyline points="20,24 28,32 36,24" />
      <line x1="28" y1="12" x2="28" y2="32" />
      <line x1="12" y1="46" x2="44" y2="46" />
    </g>
    <text x="955" y="333" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">Pull</text>
  </g>

  <!-- Flow arrow 4 -> 5 -->
  <line x1="1055" y1="324" x2="1067" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 5: Container start -->
  <g id="seg-container-start">
    <rect x="1070" y="270" width="245" height="108" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Application window / process start icon -->
    <g transform="translate(1080, 296)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="6" />
      <line x1="6" y1="20" x2="50" y2="20" />
      <polygon points="22,28 36,36 22,44" fill="#207448" stroke="none" />
    </g>
    <text x="1200" y="322" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="1200" dy="0">Container</tspan>
      <tspan x="1200" dy="34">start</tspan>
    </text>
  </g>

  <!-- Flow arrow 5 -> 6 -->
  <line x1="1315" y1="324" x2="1327" y2="324" stroke="#207448" stroke-width="3" />

  <!-- Segment 6: Ready -->
  <g id="seg-ready">
    <rect x="1330" y="270" width="220" height="108" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Checkmark shield / ready probe icon -->
    <g transform="translate(1344, 296)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 28 C 48 40 38 48 28 52 C 18 48 8 40 8 28 V 14 Z" />
      <polyline points="18,28 25,35 38,20" />
    </g>
    <text x="1460" y="333" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Ready</text>
  </g>

  <!-- ==================== SOURCES UNDER EACH SEGMENT ==================== -->

  <!-- Connectors from timeline bar down to source cards -->
  <line x1="172" y1="378" x2="172" y2="408" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  <line x1="432" y1="378" x2="432" y2="408" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  <line x1="687" y1="378" x2="687" y2="408" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  
  <line x1="937" y1="378" x2="937" y2="408" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  <line x1="1192" y1="378" x2="1192" y2="408" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />
  <line x1="1440" y1="378" x2="1440" y2="408" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />

  <!-- Left Column Group: Sources 1, 2, 3 -->
  <!-- Card 1: Created to Scheduled Source -->
  <g id="card-src-1">
    <rect x="50" y="415" width="725" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(75, 454)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="48" height="48" rx="6" />
      <line x1="4" y1="18" x2="52" y2="18" />
      <circle cx="16" cy="11" r="2.5" fill="#207448" />
      <circle cx="26" cy="11" r="2.5" fill="#207448" />
    </g>
    <text x="430" y="472" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="430" dy="0"><tspan font-family="monospace">creationTimestamp</tspan> versus <tspan font-family="monospace">PodScheduled</tspan></tspan>
      <tspan x="430" dy="34"><tspan font-family="monospace">lastTransitionTime,</tspan> scheduler metrics</tspan>
    </text>
  </g>

  <!-- Card 2: Scheduled to Initialized Source -->
  <g id="card-src-2">
    <rect x="50" y="570" width="725" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(75, 609)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="40" rx="4" />
      <line x1="6" y1="20" x2="50" y2="20" />
      <line x1="20" y1="20" x2="20" y2="48" />
    </g>
    <text x="430" y="628" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="430" dy="0">init containers, volume mounts, sandbox;</tspan>
      <tspan x="430" dy="34"><tspan font-family="monospace">Initialized</tspan> condition</tspan>
    </text>
  </g>

  <!-- Card 3: Sandbox Source -->
  <g id="card-src-3">
    <rect x="50" y="725" width="725" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(75, 764)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 16 L 28 6 L 50 16 L 50 44 L 28 54 L 6 44 Z" />
      <line x1="28" y1="6" x2="28" y2="54" />
    </g>
    <text x="430" y="800" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">kubelet_run_podsandbox_duration_seconds</text>
  </g>

  <!-- Right Column Group: Sources 4, 5, 6 -->
  <!-- Card 4: Pull Source -->
  <g id="card-src-4">
    <rect x="825" y="415" width="725" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(850, 454)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="44" height="36" rx="4" />
      <line x1="16" y1="20" x2="40" y2="20" />
      <line x1="16" y1="28" x2="40" y2="28" />
      <line x1="16" y1="36" x2="30" y2="36" />
    </g>
    <text x="1205" y="460" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1205" dy="0">event Pulled in X,</tspan>
      <tspan x="1205" dy="32" font-family="monospace" font-weight="bold" fill="#207448">kubelet_image_pull_duration_seconds,</tspan>
      <tspan x="1205" dy="32">containerd logs</tspan>
    </text>
  </g>

  <!-- Card 5: Container start Source -->
  <g id="card-src-5">
    <rect x="825" y="570" width="725" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(850, 609)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 38,34" />
    </g>
    <text x="1205" y="645" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan font-family="monospace">ContainersReady</tspan> time</text>
  </g>

  <!-- Card 6: Ready Source -->
  <g id="card-src-6">
    <rect x="825" y="725" width="725" height="135" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(850, 764)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 28 A 16 16 0 1 1 44 28" />
      <polyline points="28,16 28,28 36,28" />
    </g>
    <text x="1205" y="800" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">readiness probe success, <tspan font-family="monospace">Ready</tspan> condition</text>
  </g>

  <!-- ==================== BOTTOM PANELS: WARM VS COLD NODE ==================== -->

  <!-- Left: Warm node numbers -->
  <g id="panel-warm-node">
    <rect x="50" y="880" width="725" height="230" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Fast cached disk icon -->
    <g transform="translate(80, 965)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="24" />
      <path d="M 28 14 L 34 24 L 46 26 L 36 34 L 40 46 L 28 38 L 16 46 L 20 34 L 10 26 L 22 24 Z" />
    </g>
    <text x="430" y="962" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
      <tspan x="430" dy="0">API and scheduling tens of ms,</tspan>
      <tspan x="430" dy="38">sandbox and CNI 100 to 500 ms,</tspan>
      <tspan x="430" dy="38">container under 1 s</tspan>
    </text>
  </g>

  <!-- Right: Cold node numbers -->
  <g id="panel-cold-node">
    <rect x="825" y="880" width="725" height="230" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Cold cloud / network pull wait icon -->
    <g transform="translate(855, 965)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 16 40 C 10 40 6 35 6 30 C 6 25 10 21 15 21 C 16 14 22 8 30 8 C 39 8 46 15 46 24 C 49 24 52 27 52 31 C 52 36 48 40 42 40 Z" />
      <line x1="28" y1="28" x2="28" y2="46" />
      <polyline points="22,40 28,46 34,40" />
    </g>
    <text x="1205" y="962" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1205" dy="0">pull and unpack minutes,</tspan>
      <tspan x="1205" dy="38">PVC attach 5 to 60 s,</tspan>
      <tspan x="1205" dy="38">model load minutes</tspan>
    </text>
  </g>

</svg>'''

open("test_candidate.svg", "w").write(svg_code)
print("Updated test_candidate.svg with perfect heights and paddings!")
