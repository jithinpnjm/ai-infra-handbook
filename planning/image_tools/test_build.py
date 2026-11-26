import subprocess
from verify_stream_svg import test_svg

svg_template = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1010" width="1600" height="1010">
  <title>A silent stream is reset by the middlebox; a heartbeat keeps it alive</title>
  <desc>A horizontal timeline illustrating how a silent client connection is closed by a middlebox after an idle timeout and encounters reset or BrokenPipe on the next write, whereas a heartbeat client sending ping keeps the flow still alive.</desc>

  <defs>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1010" fill="#f5f8f5" />

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">A silent stream is reset by the middlebox; </tspan>
    <tspan x="800" dy="54">a heartbeat keeps it alive</tspan>
  </text>

  <!-- ==================== TIME MARKERS ==================== -->
  <line x1="380" y1="182" x2="1480" y2="182" stroke="#b8c9c0" stroke-width="2" />

  <!-- 0 seconds -->
  <line x1="430" y1="172" x2="430" y2="192" stroke="#207448" stroke-width="3" />
  <text x="430" y="162" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">0 seconds</text>

  <!-- 0.3 seconds -->
  <line x1="750" y1="172" x2="750" y2="192" stroke="#207448" stroke-width="3" />
  <text x="750" y="162" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">0.3 seconds</text>

  <!-- 0.6 seconds -->
  <line x1="1070" y1="172" x2="1070" y2="192" stroke="#207448" stroke-width="3" />
  <text x="1070" y="162" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">0.6 seconds</text>

  <!-- the next write -->
  <line x1="1390" y1="172" x2="1390" y2="192" stroke="#207448" stroke-width="3" />
  <text x="1390" y="162" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">the next write</text>

  <!-- ==================== TOP LANE: silent client ==================== -->
  <rect x="40" y="202" width="1520" height="216" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <!-- Silent client header box -->
  <rect x="55" y="217" width="250" height="186" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  <g transform="translate(152, 237)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="34" rx="4" />
    <line x1="18" y1="48" x2="38" y2="48" />
    <line x1="28" y1="40" x2="28" y2="48" />
  </g>
  <text x="180" y="342" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">silent client</text>

  <!-- Silent track baseline -->
  <line x1="380" y1="330" x2="1240" y2="330" stroke="#d0ded4" stroke-width="4" stroke-dasharray="4 4" />

  <!-- Dot at 0: last byte -->
  <circle cx="430" cy="330" r="10" fill="#207448" stroke="#303a36" stroke-width="2" />
  <text x="430" y="280" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">last byte</text>

  <!-- Grey band: quiet for longer than the idle timeout -->
  <rect x="460" y="295" width="530" height="70" rx="8" fill="#e3e8e5" stroke="#a0aba5" stroke-width="2" stroke-dasharray="6 4" />
  <text x="725" y="325" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="725" dy="0">quiet for longer </tspan>
    <tspan x="725" dy="28">than the idle timeout</tspan>
  </text>

  <!-- Middlebox icon at about 0.6: middlebox closes idle flow -->
  <rect x="1030" y="295" width="80" height="70" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(1042, 302)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="8" width="44" height="40" rx="6" />
    <line x1="14" y1="28" x2="42" y2="28" />
    <polyline points="34,20 42,28 34,36" />
    <polyline points="22,20 14,28 22,36" />
  </g>
  <text x="1070" y="250" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
    <tspan x="1070" dy="0">middlebox closes </tspan>
    <tspan x="1070" dy="26">idle flow</tspan>
  </text>

  <!-- Orange failure arrow at the next write: reset or BrokenPipe -->
  <rect x="1235" y="240" width="270" height="52" rx="8" fill="#fff5ed" stroke="#db8129" stroke-width="2.5" />
  <text x="1370" y="274" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">
    <tspan>reset or </tspan><tspan font-family="monospace">BrokenPipe</tspan>
  </text>
  <line x1="1245" y1="330" x2="1450" y2="330" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />

  <!-- ==================== CAPTURE STRIP ==================== -->
  <rect x="40" y="428" width="1520" height="82" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <g transform="translate(60, 441)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="8" width="44" height="40" rx="4" />
    <polyline points="14,22 22,28 14,34" />
    <line x1="26" y1="36" x2="38" y2="36" />
  </g>
  <text x="820" y="462" text-anchor="middle" font-family="monospace" font-size="24" fill="#303a36">
    <tspan x="820" dy="0">Flags [F.] from the server, then ack from the client, </tspan>
    <tspan x="820" dy="28">then silence, then Flags [R] at the next client write</tspan>
  </text>

  <!-- ==================== BOTTOM LANE: heartbeat client ==================== -->
  <rect x="40" y="520" width="1520" height="216" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <!-- Heartbeat client header box -->
  <rect x="55" y="535" width="250" height="186" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  <g transform="translate(152, 555)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="34" rx="4" />
    <line x1="18" y1="48" x2="38" y2="48" />
    <line x1="28" y1="40" x2="28" y2="48" />
  </g>
  <text x="180" y="660" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">heartbeat client</text>

  <!-- Green pulses at 0, 0.3, 0.6: ping every half the idle timeout -->
  <text x="750" y="580" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan font-family="monospace">ping</tspan><tspan> every half the idle timeout</tspan>
  </text>

  <!-- Pulse 1 at 0 seconds (x = 430) -->
  <polyline points="400,648 420,648 425,622 430,674 435,636 440,648 460,648" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round" />

  <!-- Line connecting pulse 1 to pulse 2 -->
  <line x1="460" y1="648" x2="720" y2="648" stroke="#207448" stroke-width="4" />

  <!-- Pulse 2 at 0.3 seconds (x = 750) -->
  <polyline points="720,648 740,648 745,622 750,674 755,636 760,648 780,648" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round" />

  <!-- Line connecting pulse 2 to pulse 3 -->
  <line x1="780" y1="648" x2="1040" y2="648" stroke="#207448" stroke-width="4" />

  <!-- Pulse 3 at 0.6 seconds (x = 1070) -->
  <polyline points="1040,648 1060,648 1065,622 1070,674 1075,636 1080,648 1100,648" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round" />

  <!-- Green line continuing with label still alive -->
  <line x1="1100" y1="648" x2="1490" y2="648" stroke="#207448" stroke-width="4" stroke-linecap="round" />
  <rect x="1270" y="570" width="200" height="48" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <text x="1370" y="602" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">still alive</text>

  <!-- ==================== VERTICAL DASHED LINE: idle timeout ==================== -->
  <line x1="1070" y1="192" x2="1070" y2="736" stroke="#207448" stroke-width="3" stroke-dasharray="8 6" />
  <rect x="980" y="180" width="180" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <text x="1070" y="205" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">idle timeout</text>

  <!-- ==================== NUMBERED STEPS ==================== -->
  <!-- Step 1 -->
  <rect x="40" y="750" width="480" height="120" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <circle cx="82" cy="810" r="24" fill="#207448" />
  <text x="82" y="819" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
  <text x="125" y="796" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="125" dy="0">find the lowest idle </tspan>
    <tspan x="125" dy="28">timeout on the path</tspan>
  </text>

  <!-- Step 2 -->
  <rect x="560" y="750" width="480" height="120" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <circle cx="602" cy="810" r="24" fill="#207448" />
  <text x="602" y="819" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
  <text x="645" y="796" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="645" dy="0">send a heartbeat </tspan>
    <tspan x="645" dy="28">below it with margin</tspan>
  </text>

  <!-- Step 3 -->
  <rect x="1080" y="750" width="480" height="120" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <circle cx="1122" cy="810" r="24" fill="#207448" />
  <text x="1122" y="819" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
  <text x="1165" y="796" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1165" dy="0">check no hard total </tspan>
    <tspan x="1165" dy="28">duration limit applies</tspan>
  </text>

  <!-- ==================== GREEN TAKEAWAY BAR ==================== -->
  <rect x="40" y="890" width="1520" height="70" rx="10" fill="#207448" />
  <text x="800" y="934" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">The reset appears only when the client speaks again, so a silent stream looks fine until its next write.</text>
</svg>'''

test_svg(svg_template)
