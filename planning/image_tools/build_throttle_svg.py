import re
import xml.etree.ElementTree as ET

# Construct the SVG
svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
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
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Detecting throttling, and why thread pools</tspan>
    <tspan x="800" dy="56">sized from nproc make it worse</tspan>
  </text>

  <!-- ==================== LEFT PANEL: Detect throttling ==================== -->
  <g id="left-panel">
    <!-- Panel container -->
    <rect x="40" y="140" width="740" height="690" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Left Panel Header Box -->
    <rect x="65" y="160" width="690" height="70" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Gauge / Meter (56px) -->
    <g transform="translate(85, 167)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 42 A 22 22 0 1 1 46 42"/>
      <circle cx="28" cy="40" r="4" fill="#207448"/>
      <line x1="28" y1="40" x2="38" y2="24"/>
      <line x1="28" y1="48" x2="28" y2="52"/>
    </g>
    <text x="160" y="206" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Detect throttling</text>

    <!-- Card 1: cpu.stat fields -->
    <g id="card-cpustat">
      <rect x="65" y="245" width="690" height="155" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Chip / Stats (56px) -->
      <g transform="translate(85, 255)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
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
        <tspan x="160" y="285">usage_usec, user_usec, system_usec,</tspan>
        <tspan x="160" y="325">nr_periods, nr_throttled,</tspan>
        <tspan x="160" y="365">throttled_usec, nr_bursts, burst_usec</tspan>
      </text>
    </g>

    <!-- Card 2: Rule -->
    <g id="card-rule">
      <rect x="65" y="415" width="690" height="115" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Checkmark / Scale / Rule (56px) -->
      <g transform="translate(85, 444)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22"/>
        <polyline points="18,28 25,36 38,20"/>
      </g>
      <text font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
        <tspan x="160" y="464">compare nr_throttled with nr_periods</tspan>
        <tspan x="160" y="500">and check throttled_usec</tspan>
      </text>
    </g>

    <!-- Card 3: cAdvisor metrics -->
    <g id="card-cadvisor">
      <rect x="65" y="545" width="690" height="145" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Pulse / Activity (56px) -->
      <g transform="translate(85, 560)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="44" height="40" rx="6"/>
        <polyline points="12,28 20,28 25,18 31,38 36,28 44,28"/>
      </g>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="85" y="632">container_cpu_cfs_throttled_periods_total</tspan>
        <tspan x="85" y="668">and container_cpu_cfs_periods_total</tspan>
      </text>
    </g>

    <!-- Card 4: cpu.pressure (PSI) -->
    <g id="card-psi">
      <rect x="65" y="705" width="690" height="105" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Pressure Dial (56px) -->
      <g transform="translate(85, 730)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22"/>
        <line x1="28" y1="28" x2="38" y2="16"/>
        <circle cx="28" cy="28" r="4" fill="#207448"/>
      </g>
      <text x="160" y="768" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">cpu.pressure (PSI)</text>
    </g>
  </g>

  <!-- ==================== RIGHT PANEL: The oversubscription trap ==================== -->
  <g id="right-panel">
    <!-- Panel container -->
    <rect x="820" y="140" width="740" height="690" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Right Panel Header Box -->
    <rect x="845" y="160" width="690" height="70" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Gear / Service (56px) -->
    <g transform="translate(865, 167)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10"/>
      <path d="M 28 6 L 28 12 M 28 44 L 28 50 M 6 28 L 12 28 M 44 28 L 50 28 M 12 12 L 17 17 M 39 39 L 44 44 M 12 44 L 17 39 M 39 17 L 44 12"/>
    </g>
    <text x="940" y="206" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">The oversubscription trap</text>

    <!-- Host Box: 64 CPUs -->
    <g id="box-host">
      <rect x="845" y="245" width="690" height="190" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      
      <!-- Host header with Server Icon -->
      <g transform="translate(865, 255)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="44" height="16" rx="4"/>
        <circle cx="14" cy="16" r="2.5" fill="#207448"/>
        <line x1="22" y1="16" x2="42" y2="16"/>
        <rect x="6" y="30" width="44" height="16" rx="4"/>
        <circle cx="14" cy="38" r="2.5" fill="#207448"/>
        <line x1="22" y1="38" x2="42" y2="38"/>
      </g>
      <text x="935" y="288" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">64 CPUs</text>

      <!-- Inside Container Box -->
      <rect x="865" y="310" width="650" height="110" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <text x="885" y="348" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">cpu.max = 200000 100000 (2 CPUs)</text>

      <!-- Runtime reads nproc = 64 (orange highlight badge) -->
      <rect x="885" y="360" width="220" height="48" rx="8" fill="#fff9f5" stroke="#db8129" stroke-width="2.5"/>
      <text x="995" y="394" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129">nproc = 64</text>

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
    <line x1="1190" y1="435" x2="1190" y2="455" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)"/>

    <!-- Result Card -->
    <g id="card-result">
      <rect x="845" y="455" width="690" height="120" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Timer Pause (56px) -->
      <g transform="translate(865, 487)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="28" cy="28" r="22"/>
        <line x1="22" y1="18" x2="22" y2="38"/>
        <line x1="34" y1="18" x2="34" y2="38"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="940" y="482">the quota is burned early in each period,</tspan>
        <tspan x="940" y="518">then every thread pauses even though</tspan>
        <tspan x="940" y="554">other CPUs are idle</tspan>
      </text>
    </g>

    <!-- Fix Table Box -->
    <g id="box-fix-table">
      <rect x="845" y="590" width="690" height="225" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      
      <!-- Horizontal divider lines between table rows -->
      <line x1="845" y1="645" x2="1535" y2="645" stroke="#e8f1ea" stroke-width="2"/>
      <line x1="845" y1="700" x2="1535" y2="700" stroke="#e8f1ea" stroke-width="2"/>
      <line x1="845" y1="755" x2="1535" y2="755" stroke="#e8f1ea" stroke-width="2"/>

      <!-- Fix 1: Go -->
      <text x="875" y="627" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">Go: automaxprocs (GOMAXPROCS)</text>

      <!-- Fix 2: Java -->
      <text x="875" y="682" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">Java: -XX:ActiveProcessorCount</text>

      <!-- Fix 3: OpenMP -->
      <text x="875" y="737" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">OpenMP: OMP_NUM_THREADS</text>

      <!-- Fix 4: Python -->
      <text font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">
        <tspan x="875" y="781">Python: os.cpu_count() reports the host,</tspan>
        <tspan x="875" y="805">pass the limit in</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== FOOTER CARDS ==================== -->
  <g id="footer-cards">
    <!-- Footer Card 1: Kernel 5.4 slice-expiry fix -->
    <g id="footer-card-1">
      <rect x="40" y="855" width="486" height="235" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Shield / Kernel (56px) -->
      <g transform="translate(60, 875)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 28 6 L 48 14 V 28 C 48 42 28 52 28 52 C 28 52 8 42 8 28 V 14 Z"/>
        <polyline points="20,28 26,34 38,20"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="130" y="905">Kernels before 5.4</tspan>
        <tspan x="60" y="948">(slice-expiry fix) could</tspan>
        <tspan x="60" y="984">throttle even with unused</tspan>
        <tspan x="60" y="1020">quota: use a recent kernel</tspan>
      </text>
    </g>

    <!-- Footer Card 2: cpu.max.burst -->
    <g id="footer-card-2">
      <rect x="557" y="855" width="486" height="235" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Lightning / Burst (56px) -->
      <g transform="translate(577, 875)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 32 4 L 14 28 L 28 28 L 22 52 L 42 24 L 28 24 Z"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="647" y="905" font-family="monospace">cpu.max.burst</tspan>
        <tspan x="577" y="948">(kernel 5.14 and later)</tspan>
        <tspan x="577" y="984">lets a group save unused</tspan>
        <tspan x="577" y="1020">quota for short bursts</tspan>
      </text>
    </g>

    <!-- Footer Card 3: Container nproc /proc/cpuinfo -->
    <g id="footer-card-3">
      <rect x="1074" y="855" width="486" height="235" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Window / Container (56px) -->
      <g transform="translate(1094, 875)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="8" y="10" width="40" height="36" rx="6"/>
        <line x1="8" y1="20" x2="48" y2="20"/>
        <circle cx="16" cy="15" r="2" fill="#207448"/>
        <circle cx="22" cy="15" r="2" fill="#207448"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1164" y="905">Inside a container,</tspan>
        <tspan x="1094" y="944">nproc and /proc/cpuinfo</tspan>
        <tspan x="1094" y="978">still show the host unless</tspan>
        <tspan x="1094" y="1012">you use lxcfs or a runtime</tspan>
        <tspan x="1094" y="1046">that understands limits</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1110" width="1520" height="65" rx="12" fill="#207448"/>
    <!-- Icon: Check Shield (white) -->
    <g transform="translate(65, 1118)" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 24 6 L 44 14 V 26 C 44 38 24 46 24 46 C 24 46 4 38 4 26 V 14 Z"/>
      <polyline points="15,25 21,31 33,19"/>
    </g>
    <text x="125" y="1152" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">Average usage can look healthy while the pauses hide inside each period</text>
  </g>
</svg>'''

with open("candidate_throttling.svg", "w") as f:
    f.write(svg)
print("Saved candidate_throttling.svg")
