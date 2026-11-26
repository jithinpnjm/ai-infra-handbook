const fs = require('fs');

const requiredLabels = [
  "Words that sound alike: bandwidth versus throughput, latency versus response time, and why 98 to 99 percent matters",
  "Bandwidth: the maximum possible throughput",
  "Throughput: the rate actually achieved; a link with plenty of bandwidth can deliver poor throughput if work arrives in bursts",
  "Latency: time an operation waits before service starts",
  "Service time",
  "Response time: waiting plus service",
  "Utilisation: fraction of an interval a resource was busy",
  "Saturation: work that cannot be serviced yet and waits in a queue",
  "a device can be 100% busy and still accept more work: busy and full are different, an NVMe drive with a deep queue",
  "IOPS: operations per second",
  "Cache hit ratio is not linear in benefit",
  "98% to 99%",
  "half as many misses",
  "10% to 11%",
  "almost no change",
  "A miss costs the same either way, so what matters is how many misses are left",
  "Say each number with its unit and its interval: tokens per second per GPU, averaged over a stated interval",
  "Agree on these terms with the people who will read your numbers"
];

// Let us construct the SVG
const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Words that sound alike: bandwidth versus throughput, latency versus response time, and why 98 to 99 percent matters</title>
  <desc>Visual infographic comparing bandwidth and throughput, latency and response time, utilisation and saturation, IOPS, and explaining why cache hit ratio improvements from 98% to 99% matter non-linearly.</desc>

  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 1 L 9 5 L 0 9 z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Title (48px bold, wrapped onto 3 lines) -->
  <text x="800" y="52" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="800" dy="0">Words that sound alike: bandwidth versus throughput,</tspan>
    <tspan x="800" dy="52">latency versus response time,</tspan>
    <tspan x="800" dy="52">and why 98 to 99 percent matters</tspan>
  </text>

  <!-- LEFT HALF: Four definition pairs as paired cards -->

  <!-- Card 1: Bandwidth & Throughput (y: 185 to 395, h: 210) -->
  <rect x="40" y="185" width="740" height="210" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  
  <!-- Icon 1: Network Pipe / Flow Gauge (outline, 56px, stroke 4, green) -->
  <g transform="translate(60, 202)">
    <rect x="2" y="14" width="52" height="28" rx="6" fill="none" stroke="#207448" stroke-width="4"/>
    <path d="M 12 28 L 44 28" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    <path d="M 34 20 L 44 28 L 34 36" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  </g>

  <!-- Bandwidth Label -->
  <text x="135" y="226" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
    <tspan x="135" dy="0">Bandwidth: the maximum</tspan>
    <tspan x="135" dy="30">possible throughput</tspan>
  </text>

  <!-- Throughput Box & Label -->
  <rect x="60" y="278" width="700" height="102" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="80" y="306" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="80" dy="0">Throughput: the rate actually achieved;</tspan>
    <tspan x="80" dy="30">a link with plenty of bandwidth can deliver</tspan>
    <tspan x="80" dy="30">poor throughput if work arrives in bursts</tspan>
  </text>

  <!-- Card 2: Latency + Service time = Response time (y: 410 to 635, h: 225) -->
  <rect x="40" y="410" width="740" height="225" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  
  <!-- Icon 2: Clock / Timer (outline, 56px, stroke 4, green) -->
  <g transform="translate(60, 424)">
    <circle cx="28" cy="28" r="24" fill="none" stroke="#207448" stroke-width="4"/>
    <polyline points="28,14 28,28 38,28" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  </g>

  <!-- Joined Bar: Segment 1 (Latency) + Segment 2 (Service time) -->
  <rect x="60" y="492" width="455" height="72" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="76" y="522" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="76" dy="0">Latency: time an operation</tspan>
    <tspan x="76" dy="30">waits before service starts</tspan>
  </text>

  <rect x="525" y="492" width="235" height="72" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="545" y="537" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="545" dy="0">Service time</tspan>
  </text>

  <!-- Joined Bar Container: Response time -->
  <rect x="60" y="572" width="700" height="50" rx="6" fill="#207448"/>
  <text x="410" y="606" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff" text-anchor="middle">
    <tspan x="410" dy="0">Response time: waiting plus service</tspan>
  </text>

  <!-- Card 3: Utilisation vs Saturation (y: 650 to 940, h: 290) -->
  <rect x="40" y="650" width="740" height="290" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

  <!-- Icon 3: Disk Cylinder (outline, 56px, stroke 4, green) -->
  <g transform="translate(60, 666)">
    <ellipse cx="28" cy="14" rx="24" ry="10" fill="none" stroke="#207448" stroke-width="4"/>
    <path d="M 4 14 L 4 42 A 24 10 0 0 0 52 42 L 52 14" fill="none" stroke="#207448" stroke-width="4"/>
    <path d="M 4 28 A 24 10 0 0 0 52 28" fill="none" stroke="#207448" stroke-width="4"/>
  </g>

  <!-- Utilisation Box & Label -->
  <rect x="135" y="664" width="625" height="66" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="150" y="692" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="150" dy="0">Utilisation: fraction of an interval</tspan>
    <tspan x="150" dy="28">a resource was busy</tspan>
  </text>

  <!-- Saturation Box & Label -->
  <rect x="60" y="738" width="700" height="66" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="76" y="766" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="76" dy="0">Saturation: work that cannot be serviced yet</tspan>
    <tspan x="76" dy="28">and waits in a queue</tspan>
  </text>

  <!-- Device Note Box & Label -->
  <rect x="60" y="812" width="700" height="114" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
  <text x="76" y="842" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="76" dy="0">a device can be 100% busy and still</tspan>
    <tspan x="76" dy="30">accept more work: busy and full are</tspan>
    <tspan x="76" dy="30">different, an NVMe drive with a deep queue</tspan>
  </text>

  <!-- Card 4: IOPS (y: 955 to 1035, h: 80) -->
  <rect x="40" y="955" width="740" height="80" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  
  <!-- Icon 4: Chip / CPU (outline, 56px, stroke 4, green) -->
  <g transform="translate(60, 967)">
    <rect x="12" y="12" width="32" height="32" rx="4" fill="none" stroke="#207448" stroke-width="4"/>
    <line x1="20" y1="2" x2="20" y2="10" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    <line x1="36" y1="2" x2="36" y2="10" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    <line x1="20" y1="46" x2="20" y2="54" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    <line x1="36" y1="46" x2="36" y2="54" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    <line x1="2" y1="20" x2="10" y2="20" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    <line x1="2" y1="36" x2="10" y2="36" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    <line x1="46" y1="20" x2="54" y2="20" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    <line x1="46" y1="36" x2="54" y2="36" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
  </g>

  <!-- IOPS Label -->
  <text x="135" y="1005" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
    <tspan x="135" dy="0">IOPS: operations per second</tspan>
  </text>

  <!-- RIGHT HALF: Cache hit ratio is not linear in benefit (y: 185 to 1035, h: 850) -->
  <rect x="820" y="185" width="740" height="850" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

  <!-- Icon 5: Cache Memory Hierarchy (outline, 56px, stroke 4, green) -->
  <g transform="translate(845, 205)">
    <rect x="4" y="6" width="48" height="12" rx="3" fill="none" stroke="#207448" stroke-width="4"/>
    <rect x="4" y="22" width="48" height="12" rx="3" fill="none" stroke="#207448" stroke-width="4"/>
    <rect x="4" y="38" width="48" height="12" rx="3" fill="none" stroke="#207448" stroke-width="4"/>
  </g>

  <!-- Right Half Title (Node title >= 30px bold) -->
  <text x="918" y="235" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="918" dy="0">Cache hit ratio is not</tspan>
    <tspan x="918" dy="38">linear in benefit</tspan>
  </text>

  <!-- Bar A Container (98% to 99%) -->
  <rect x="845" y="310" width="690" height="270" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>

  <!-- Bar A Header: '98% to 99%' -->
  <text x="870" y="348" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">
    <tspan x="870" dy="0">98% to 99%</tspan>
  </text>

  <!-- Bar A: 100 accesses visual bars -->
  <!-- Access Bar 1: 98% hit (2 misses) -->
  <g transform="translate(870, 375)">
    <rect x="0" y="0" width="400" height="30" rx="4" fill="#d2e5d5"/>
    <rect x="0" y="0" width="392" height="30" rx="4" fill="#207448"/>
    <rect x="392" y="0" width="8" height="30" fill="#303a36"/>
  </g>
  <!-- Access Bar 2: 99% hit (1 miss) -->
  <g transform="translate(870, 420)">
    <rect x="0" y="0" width="400" height="30" rx="4" fill="#d2e5d5"/>
    <rect x="0" y="0" width="396" height="30" rx="4" fill="#207448"/>
    <rect x="396" y="0" width="4" height="30" fill="#303a36"/>
  </g>

  <!-- Misses shrinking visualization: 2 dots -> 1 dot -->
  <g transform="translate(870, 480)">
    <!-- 2 dots -->
    <circle cx="16" cy="18" r="10" fill="#303a36"/>
    <circle cx="44" cy="18" r="10" fill="#303a36"/>
    <!-- Transition Arrow -->
    <line x1="70" y1="18" x2="110" y2="18" stroke="#207448" stroke-width="4" marker-end="url(#arrow)"/>
    <!-- 1 dot -->
    <circle cx="136" cy="18" r="10" fill="#303a36"/>
  </g>

  <!-- Label 'half as many misses' (orange #db8129, single highlight) -->
  <text x="870" y="552" font-family="sans-serif" font-size="28" font-weight="bold" fill="#db8129">
    <tspan x="870" dy="0">half as many misses</tspan>
  </text>

  <!-- Bar B Container (10% to 11%) -->
  <rect x="845" y="605" width="690" height="235" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>

  <!-- Bar B Header: '10% to 11%' -->
  <text x="870" y="643" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">
    <tspan x="870" dy="0">10% to 11%</tspan>
  </text>

  <!-- Bar B: 100 accesses visual bars -->
  <!-- Access Bar 1: 10% hit (90 misses) -->
  <g transform="translate(870, 670)">
    <rect x="0" y="0" width="400" height="30" rx="4" fill="#303a36"/>
    <rect x="0" y="0" width="40" height="30" rx="4" fill="#207448"/>
  </g>
  <!-- Access Bar 2: 11% hit (89 misses) -->
  <g transform="translate(870, 715)">
    <rect x="0" y="0" width="400" height="30" rx="4" fill="#303a36"/>
    <rect x="0" y="0" width="44" height="30" rx="4" fill="#207448"/>
  </g>

  <!-- Label 'almost no change' -->
  <text x="870" y="795" font-family="sans-serif" font-size="26" fill="#303a36">
    <tspan x="870" dy="0">almost no change</tspan>
  </text>

  <!-- Rule Box Container -->
  <rect x="845" y="865" width="690" height="145" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="870" y="922" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="870" dy="0">A miss costs the same either way, so what</tspan>
    <tspan x="870" dy="34">matters is how many misses are left</tspan>
  </text>

  <!-- BOTTOM STRIP (y: 1050 to 1115, h: 65) -->
  <rect x="40" y="1050" width="1520" height="65" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  
  <!-- Icon: Unit & Interval Gauge (56px) -->
  <g transform="translate(56, 1054)">
    <circle cx="28" cy="28" r="22" fill="none" stroke="#207448" stroke-width="4"/>
    <path d="M 14 36 A 16 16 0 1 1 42 36" fill="none" stroke="#207448" stroke-width="3"/>
    <line x1="28" y1="28" x2="38" y2="18" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
  </g>

  <text x="130" y="1076" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="130" dy="0">Say each number with its unit and its interval:</tspan>
    <tspan x="130" dy="26">tokens per second per GPU, averaged over a stated interval</tspan>
  </text>

  <!-- BOTTOM BAR: Takeaway Bar (y: 1125 to 1180, h: 55) -->
  <rect x="40" y="1125" width="1520" height="55" rx="8" fill="#207448"/>
  
  <!-- Icon: Handshake / Agreement outline (56px, stroke white) -->
  <g transform="translate(56, 1124)">
    <circle cx="28" cy="28" r="22" fill="none" stroke="#ffffff" stroke-width="3"/>
    <polyline points="18,28 25,35 38,20" fill="none" stroke="#ffffff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>
  </g>

  <text x="130" y="1161" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
    <tspan x="130" dy="0">Agree on these terms with the people who will read your numbers</tspan>
  </text>
</svg>`;

fs.writeFileSync('test.svg', svg);
console.log('SVG written to test.svg');
