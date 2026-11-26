import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Detecting throttling, and why thread pools sized from nproc make it worse</title>
  <desc>Visual infographic explaining CPU throttling detection using cpu.stat, cAdvisor, and PSI, the oversubscription trap caused by thread pools sized from nproc on high-core hosts, language-specific fixes, and kernel burst features.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- ==================== DIAGRAM TITLE ==================== -->
  <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Detecting throttling, and why thread pools</tspan>
    <tspan x="800" dy="54">sized from nproc make it worse</tspan>
  </text>

  <!-- ==================== LEFT PANEL: Detect throttling ==================== -->
  <g id="left-panel">
    <!-- Panel container -->
    <rect x="40" y="135" width="740" height="695" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Left Panel Header Box -->
    <rect x="65" y="155" width="690" height="70" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Gauge / Meter (56px) -->
    <g transform="translate(85, 162)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 42 A 22 22 0 1 1 46 42"/>
      <circle cx="28" cy="40" r="4" fill="#207448"/>
      <line x1="28" y1="40" x2="38" y2="24"/>
      <line x1="28" y1="48" x2="28" y2="52"/>
    </g>
    <text x="160" y="201" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Detect throttling</text>

    <!-- Card 1: cpu.stat fields -->
    <g id="card-cpustat">
      <rect x="65" y="240" width="690" height="150" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Chip / Stats (56px) -->
      <g transform="translate(85, 248)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="8" width="40" height="40" rx="6"/>
        <rect x="18" y="18" width="20" height="20" rx="3"/>
        <line x1="18" y1="2" x2="18" y2="8"/>
        <line x1="28" y1="2" x2="28" y2="8"/>
        <line x1="38" y1="2" x2="38" y2="8"/>
        <line x1="18" y1="48" x2="18" y2="54"/>
        <line x1="28" y1="48" x2="28" y2="54"/>
        <line x1="38" y1="48" x2="38" y2="54"/>
        <line x1="2" y1="18" x2="8" y2="18"/>
        <line x1="2" y1="28" x2="8" y2="28"/>
        <line x1="2" y1="38" x2="8" y2="38"/>
        <line x1="48" y1="18" x2="54" y2="18"/>
        <line x1="48" y1="28" x2="54" y2="28"/>
        <line x1="48" y1="38" x2="54" y2="38"/>
      </g>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="160" y="278">usage_usec, user_usec, system_usec,</tspan>
        <tspan x="160" y="318">nr_periods, nr_throttled,</tspan>
        <tspan x="160" y="358">throttled_usec, nr_bursts, burst_usec</tspan>
      </text>
    </g>

    <!-- Card 2: Rule -->
    <g id="card-rule">
      <rect x="65" y="405" width="690" height="110" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Checkmark / Rule (56px) -->
      <g transform="translate(85, 432)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22"/>
        <polyline points="18,28 25,36 38,20"/>
      </g>
      <text font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
        <tspan x="160" y="452">compare nr_throttled with nr_periods</tspan>
        <tspan x="160" y="488">and check throttled_usec</tspan>
      </text>
    </g>

    <!-- Card 3: cAdvisor metrics -->
    <g id="card-cadvisor">
      <rect x="65" y="525" width="690" height="175" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Activity / Pulse (56px) -->
      <g transform="translate(85, 540)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="44" height="40" rx="6"/>
        <polyline points="12,28 20,28 25,18 31,38 36,28 44,28"/>
      </g>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="85" y="638">container_cpu_cfs_throttled_periods_total</tspan>
        <tspan x="85" y="674">and container_cpu_cfs_periods_total</tspan>
      </text>
    </g>

    <!-- Card 4: cpu.pressure (PSI) -->
    <g id="card-psi">
      <rect x="65" y="715" width="690" height="100" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Pressure Dial (56px) -->
      <g transform="translate(85, 737)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22"/>
        <line x1="28" y1="28" x2="38" y2="16"/>
        <circle cx="28" cy="28" r="4" fill="#207448"/>
      </g>
      <text x="160" y="771" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">cpu.pressure (PSI)</text>
    </g>
  </g>

  <!-- ==================== RIGHT PANEL: The oversubscription trap ==================== -->
  <g id="right-panel">
    <!-- Panel container -->
    <rect x="820" y="135" width="740" height="695" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Right Panel Header Box -->
    <rect x="845" y="155" width="690" height="70" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Gear (56px) -->
    <g transform="translate(865, 162)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10"/>
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12 12 L 17 17 M 39 39 L 44 44 M 12 44 L 17 39 M 39 17 L 44 12"/>
    </g>
    <text x="945" y="201" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">The oversubscription trap</text>

    <!-- Host Box: 64 CPUs -->
    <g id="box-host">
      <rect x="845" y="240" width="690" height="195" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      
      <!-- Host header with Server Icon (56px) -->
      <g transform="translate(865, 248)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="44" height="16" rx="4"/>
        <circle cx="14" cy="16" r="2.5" fill="#207448"/>
        <line x1="22" y1="16" x2="42" y2="16"/>
        <rect x="6" y="30" width="44" height="16" rx="4"/>
        <circle cx="14" cy="38" r="2.5" fill="#207448"/>
        <line x1="22" y1="38" x2="42" y2="38"/>
      </g>
      <text x="945" y="283" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">64 CPUs</text>

      <!-- Inside Container Box -->
      <rect x="865" y="306" width="650" height="118" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <text x="885" y="342" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">cpu.max = 200000 100000 (2 CPUs)</text>

      <!-- Runtime reads nproc = 64 (orange highlight badge) -->
      <rect x="885" y="356" width="220" height="56" rx="8" fill="#fff9f5" stroke="#db8129" stroke-width="2.5"/>
      <text x="995" y="392" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129">nproc = 64</text>

      <!-- Visual 64-thread pool lanes illustration -->
      <g stroke="#207448" stroke-width="2" opacity="0.6">
        <line x1="1130" y1="384" x2="1495" y2="384"/>
        <line x1="1145" y1="374" x2="1145" y2="394"/>
        <line x1="1180" y1="374" x2="1180" y2="394"/>
        <line x1="1215" y1="374" x2="1215" y2="394"/>
        <line x1="1250" y1="374" x2="1250" y2="394"/>
        <line x1="1285" y1="374" x2="1285" y2="394"/>
        <line x1="1320" y1="374" x2="1320" y2="394"/>
        <line x1="1355" y1="374" x2="1355" y2="394"/>
        <line x1="1390" y1="374" x2="1390" y2="394"/>
        <line x1="1425" y1="374" x2="1425" y2="394"/>
        <line x1="1460" y1="374" x2="1460" y2="394"/>
        <line x1="1495" y1="374" x2="1495" y2="394"/>
      </g>
    </g>

    <!-- Arrow Host Box -> Result Card -->
    <line x1="1190" y1="435" x2="1190" y2="450" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)"/>

    <!-- Result Card -->
    <g id="card-result">
      <rect x="845" y="450" width="690" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Timer / Pause (56px) -->
      <g transform="translate(865, 482)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22"/>
        <line x1="22" y1="18" x2="22" y2="38"/>
        <line x1="34" y1="18" x2="34" y2="38"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="945" y="488">the quota is burned early in each</tspan>
        <tspan x="945" y="520">period, then every thread pauses</tspan>
        <tspan x="945" y="552">even though other CPUs are idle</tspan>
      </text>
    </g>

    <!-- Fix Table Box -->
    <g id="box-fix-table">
      <rect x="845" y="585" width="690" height="235" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      
      <!-- Horizontal divider lines between table rows -->
      <line x1="845" y1="638" x2="1535" y2="638" stroke="#e8f1ea" stroke-width="2"/>
      <line x1="845" y1="691" x2="1535" y2="691" stroke="#e8f1ea" stroke-width="2"/>
      <line x1="845" y1="744" x2="1535" y2="744" stroke="#e8f1ea" stroke-width="2"/>

      <!-- Fix 1: Go -->
      <text x="875" y="621" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">Go: automaxprocs (GOMAXPROCS)</text>

      <!-- Fix 2: Java -->
      <text x="875" y="674" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">Java: -XX:ActiveProcessorCount</text>

      <!-- Fix 3: OpenMP -->
      <text x="875" y="727" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">OpenMP: OMP_NUM_THREADS</text>

      <!-- Fix 4: Python -->
      <text font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">
        <tspan x="875" y="774">Python: os.cpu_count() reports the host,</tspan>
        <tspan x="875" y="802">pass the limit in</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== FOOTER CARDS ==================== -->
  <g id="footer-cards">
    <!-- Footer Card 1: Kernel 5.4 slice-expiry fix -->
    <g id="footer-card-1">
      <rect x="40" y="845" width="486" height="250" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Shield / Kernel (56px) -->
      <g transform="translate(64, 865)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 28 6 L 48 14 V 28 C 48 42 28 52 28 52 C 28 52 8 42 8 28 V 14 Z"/>
        <polyline points="20,28 26,34 38,20"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="140" y="896">Kernels before 5.4</tspan>
        <tspan x="64" y="958">(slice-expiry fix) could</tspan>
        <tspan x="64" y="992">throttle even with unused</tspan>
        <tspan x="64" y="1026">quota: use a recent kernel</tspan>
      </text>
    </g>

    <!-- Footer Card 2: cpu.max.burst -->
    <g id="footer-card-2">
      <rect x="557" y="845" width="486" height="250" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Lightning / Burst (56px) -->
      <g transform="translate(581, 865)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 32 4 L 14 28 L 28 28 L 22 52 L 42 24 L 28 24 Z"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="657" y="896" font-family="monospace">cpu.max.burst</tspan>
        <tspan x="581" y="958">(kernel 5.14 and later)</tspan>
        <tspan x="581" y="992">lets a group save unused</tspan>
        <tspan x="581" y="1026">quota for short bursts</tspan>
      </text>
    </g>

    <!-- Footer Card 3: Container nproc /proc/cpuinfo -->
    <g id="footer-card-3">
      <rect x="1074" y="845" width="486" height="250" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Window / Container (56px) -->
      <g transform="translate(1098, 865)" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="10" width="40" height="36" rx="6"/>
        <line x1="8" y1="20" x2="48" y2="20"/>
        <circle cx="16" cy="15" r="2" fill="#207448"/>
        <circle cx="22" cy="15" r="2" fill="#207448"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1174" y="888">Inside a container,</tspan>
        <tspan x="1174" y="918">nproc and /proc/cpuinfo</tspan>
        <tspan x="1098" y="958">still show the host unless</tspan>
        <tspan x="1098" y="992">you use lxcfs or a runtime</tspan>
        <tspan x="1098" y="1026">that understands limits</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1115" width="1520" height="60" rx="12" fill="#207448"/>
    <!-- Icon: Check Shield (white, 56px) -->
    <g transform="translate(64, 1117)" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 8 L 48 16 V 28 C 48 40 28 48 28 48 C 28 48 8 40 8 28 V 16 Z"/>
      <polyline points="18,28 25,34 38,20"/>
    </g>
    <text x="140" y="1153" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">Average usage can look healthy while the pauses hide inside each period</text>
  </g>
</svg>'''

with open("candidate_throttling_v3.svg", "w") as f:
    f.write(svg_content)

print("Saved candidate_throttling_v3.svg")
