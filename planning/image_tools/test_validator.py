import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Splitting a slow request into parts, with the expected values</title>
  <desc>Visual infographic explaining how to split a slow request into stages from DNS to first byte, expected latency values across distances, and diagnosing latency growth.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Splitting a slow request into parts,</tspan>
    <tspan x="800" dy="54">with the expected values</tspan>
  </text>

  <!-- ==================== TOP CONTAINER: REQUEST SPLIT ==================== -->
  <g id="request-bar-container">
    <rect x="40" y="130" width="1520" height="435" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- STAGE 1: Name lookup (DNS) -->
    <g id="stage-dns">
      <rect x="60" y="150" width="264" height="240" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Number Circle 1 -->
      <circle cx="95" cy="185" r="22" fill="#207448"/>
      <text x="95" y="193" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>
      <!-- Icon: Search / DNS Globe (outline 44px) -->
      <g transform="translate(130, 163)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="20" cy="20" r="16"/>
        <line x1="32" y1="32" x2="42" y2="42"/>
        <line x1="4" y1="20" x2="36" y2="20"/>
      </g>
      <!-- Labels -->
      <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="80" y="242">Name lookup</tspan>
        <tspan x="80" y="276">(DNS):</tspan>
      </text>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="80" y="310">dig +stats,</tspan>
      </text>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="80" y="342">can time out</tspan>
        <tspan x="80" y="372">for tens of seconds</tspan>
      </text>
    </g>

    <!-- Arrow 1 -> 2 -->
    <line x1="324" y1="270" x2="342" y2="270" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)"/>

    <!-- STAGE 2: Path round trip -->
    <g id="stage-rtt">
      <rect x="342" y="150" width="250" height="240" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Number Circle 2 -->
      <circle cx="377" cy="185" r="22" fill="#207448"/>
      <text x="377" y="193" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>
      <!-- Icon: Path / Two Way Arrows (outline 44px) -->
      <g transform="translate(412, 163)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="14" x2="38" y2="14"/>
        <polyline points="28,6 38,14 28,22"/>
        <line x1="38" y1="30" x2="4" y2="30"/>
        <polyline points="14,22 4,30 14,38"/>
      </g>
      <!-- Labels -->
      <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="362" y="242">Path round</tspan>
        <tspan x="362" y="276">trip:</tspan>
      </text>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="362" y="316">ping, mtr,</tspan>
        <tspan x="362" y="356">rtt in ss -ti</tspan>
      </text>
    </g>

    <!-- Arrow 2 -> 3 -->
    <line x1="592" y1="270" x2="610" y2="270" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)"/>

    <!-- STAGE 3: TCP connection (handshake) -->
    <g id="stage-tcp">
      <rect x="610" y="150" width="280" height="240" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Number Circle 3 -->
      <circle cx="645" cy="185" r="22" fill="#207448"/>
      <text x="645" y="193" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>
      <!-- Icon: Connection Handshake / Nodes (outline 44px) -->
      <g transform="translate(680, 163)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="10" cy="22" r="6"/>
        <circle cx="34" cy="22" r="6"/>
        <line x1="16" y1="22" x2="28" y2="22"/>
        <path d="M 10 16 A 14 14 0 0 1 34 16"/>
        <path d="M 10 28 A 14 14 0 0 0 34 28"/>
      </g>
      <!-- Labels -->
      <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="626" y="238">TCP</tspan>
        <tspan x="626" y="270">connection</tspan>
      </text>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="626" y="302">(handshake):</tspan>
      </text>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="626" y="334">tcpconnlat,</tspan>
        <tspan x="626" y="366">curl -w time_connect</tspan>
      </text>
    </g>

    <!-- Arrow 3 -> 4 -->
    <line x1="890" y1="270" x2="908" y2="270" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)"/>

    <!-- STAGE 4: First byte -->
    <g id="stage-firstbyte">
      <rect x="908" y="150" width="344" height="240" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Number Circle 4 -->
      <circle cx="943" cy="185" r="22" fill="#207448"/>
      <text x="943" y="193" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
      <!-- Icon: Timer / Server think time (outline 44px) -->
      <g transform="translate(980, 163)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="22" cy="22" r="18"/>
        <polyline points="22,12 22,22 30,22"/>
        <line x1="16" y1="4" x2="28" y2="4"/>
      </g>
      <!-- Labels -->
      <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="926" y="240">First byte:</tspan>
      </text>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="926" y="272">server think time</tspan>
        <tspan x="926" y="302">plus the RTT:</tspan>
      </text>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="926" y="336">curl -w</tspan>
        <tspan x="926" y="368">time_starttransfer</tspan>
      </text>
    </g>

    <!-- Arrow 4 -> 5 -->
    <line x1="1252" y1="270" x2="1270" y2="270" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)"/>

    <!-- STAGE 5: Per-request application latency -->
    <g id="stage-app">
      <rect x="1270" y="150" width="270" height="240" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Number Circle 5 -->
      <circle cx="1305" cy="185" r="22" fill="#207448"/>
      <text x="1305" y="193" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">5</text>
      <!-- Icon: Application Window / Tracing Tree (outline 44px) -->
      <g transform="translate(1342, 163)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="36" height="32" rx="4"/>
        <line x1="4" y1="16" x2="40" y2="16"/>
        <polyline points="12,24 18,30 24,24 32,24"/>
      </g>
      <!-- Labels -->
      <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
        <tspan x="1288" y="238">Per-request</tspan>
        <tspan x="1288" y="270">application</tspan>
        <tspan x="1288" y="302">latency:</tspan>
      </text>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1288" y="338">application</tspan>
        <tspan x="1288" y="368">tracing</tspan>
      </text>
    </g>

    <!-- CONNECTION LIFE SPAN BAR -->
    <g id="bar-lifespan">
      <rect x="60" y="405" width="1480" height="60" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Life span / Repeat arrows (44px) -->
      <g transform="translate(76, 413)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="22" cy="22" r="16"/>
        <polyline points="22,12 22,22 28,26"/>
      </g>
      <text x="135" y="443" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan font-weight="bold">Connection life span:</tspan> short-lived connections multiply the handshake cost
      </text>
    </g>

    <!-- TOOLS STRIP -->
    <g id="tools-strip">
      <rect x="60" y="475" width="1480" height="75" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Tools Wrench (44px) -->
      <g transform="translate(76, 490)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <path d="M 12 32 L 28 16 M 22 10 A 10 10 0 0 1 34 22 L 30 26 L 18 14 Z"/>
      </g>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="135" y="508">curl -w timing variables, dig +stats, tcpconnlat, tcpdump timestamps,</tspan>
        <tspan x="135" y="538">the rtt field from ss -ti, mtr, application tracing</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== LOWER SECTION ==================== -->
  <!-- LEFT COLUMN: STORIES & LIMITER FLAGS (x=40 to 1020, width=980) -->
  <g id="left-stories-column">
    <!-- STORY 1 -->
    <g id="story-1">
      <rect x="40" y="585" width="980" height="155" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- User / Office Diagnostic Icon (56px) -->
      <g transform="translate(60, 622)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="20" cy="16" r="10"/>
        <path d="M 6 44 C 6 32 14 28 20 28 C 26 28 34 32 34 44"/>
        <rect x="30" y="18" width="22" height="26" rx="3"/>
        <line x1="36" y1="24" x2="46" y2="24"/>
        <line x1="36" y1="30" x2="46" y2="30"/>
        <line x1="36" y1="36" x2="46" y2="36"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="135" y="628">a user says the internal app is slow, but only from one office:</tspan>
        <tspan x="135" y="666">split the wait into parts and </tspan>
        <tspan font-weight="bold" fill="#db8129">find which one grows</tspan>
        <tspan fill="#303a36"> before changing anything</tspan>
      </text>
    </g>

    <!-- STORY 2: Second story box -->
    <g id="story-2">
      <rect x="40" y="755" width="980" height="195" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- File Copy / Window Icon (56px) -->
      <g transform="translate(60, 805)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="32" height="40" rx="4"/>
        <path d="M 18 8 L 38 28"/>
        <polyline points="26,8 26,20 38,20"/>
        <polyline points="14,34 22,42 34,26"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="135" y="796">File copy starts fast then sits at a fixed speed: ss -ti shows</tspan>
        <tspan x="135" y="832" font-family="monospace">rwnd_limited</tspan>
        <tspan> as a large share of time, the receiver's window</tspan>
        <tspan x="135" y="868">is holding the sender back; fix the receiving side</tspan>
        <tspan x="135" y="904">(larger receive buffer or faster reads)</tspan>
      </text>
    </g>

    <!-- LIMITER FLAGS STRIP -->
    <g id="limiter-flags-strip">
      <rect x="40" y="965" width="980" height="135" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
      <!-- Flags / Limit Bounds Icon (56px) -->
      <g transform="translate(60, 1005)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <line x1="10" y1="8" x2="10" y2="48"/>
        <path d="M 10 12 L 38 18 L 10 28 Z"/>
        <line x1="24" y1="40" x2="48" y2="40"/>
        <circle cx="36" cy="40" r="4" fill="#207448"/>
      </g>
      <text font-family="monospace" font-size="24" fill="#303a36">
        <tspan x="135" y="1015">rwnd_limited, cwnd_limited, sndbuf_limited,</tspan>
      </text>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="135" y="1055"><tspan font-family="monospace">app_limited</tspan> tell you which factor bounds each connection</tspan>
      </text>
    </g>
  </g>

  <!-- RIGHT PANEL: Expected values (x=1040 to 1560, width=520) -->
  <g id="right-panel-expected">
    <rect x="1040" y="585" width="520" height="515" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>

    <!-- Header Box -->
    <rect x="1060" y="605" width="480" height="70" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Icon: Gauge / Target (56px) -->
    <g transform="translate(1075, 612)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <line x1="28" y1="28" x2="40" y2="16"/>
      <circle cx="28" cy="28" r="4" fill="#207448"/>
    </g>
    <text x="1150" y="652" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Expected values</text>

    <!-- Card 1: rack-local 100G -->
    <g id="card-rack-local">
      <rect x="1060" y="695" width="480" height="115" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Rack Server (44px) -->
      <g transform="translate(1075, 725)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="4" y="6" width="38" height="14" rx="3"/>
        <line x1="10" y1="13" x2="16" y2="13"/>
        <rect x="4" y="24" width="38" height="14" rx="3"/>
        <line x1="10" y1="31" x2="16" y2="31"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1135" y="742" font-family="monospace" font-weight="bold">rack-local 100G:</tspan>
        <tspan x="1135" y="780">tens of microseconds</tspan>
      </text>
    </g>

    <!-- Card 2: same-DC -->
    <g id="card-same-dc">
      <rect x="1060" y="825" width="480" height="115" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Datacenter Building (44px) -->
      <g transform="translate(1075, 855)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="8" width="34" height="32" rx="3"/>
        <line x1="14" y1="16" x2="20" y2="16"/>
        <line x1="26" y1="16" x2="32" y2="16"/>
        <line x1="14" y1="24" x2="20" y2="24"/>
        <line x1="26" y1="24" x2="32" y2="24"/>
        <line x1="18" y1="32" x2="28" y2="32"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1135" y="872" font-family="monospace" font-weight="bold">same-DC:</tspan>
        <tspan x="1135" y="910">0.2 to 0.6 ms</tspan>
      </text>
    </g>

    <!-- Card 3: cross-continent -->
    <g id="card-cross-continent">
      <rect x="1060" y="955" width="480" height="125" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Icon: Globe / Continents (44px) -->
      <g transform="translate(1075, 988)" fill="none" stroke="#207448" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="22" cy="22" r="18"/>
        <line x1="4" y1="22" x2="40" y2="22"/>
        <path d="M 22 4 A 12 18 0 0 1 22 40"/>
        <path d="M 22 4 A 12 18 0 0 0 22 40"/>
      </g>
      <text font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1135" y="1005" font-family="monospace" font-weight="bold">cross-continent:</tspan>
        <tspan x="1135" y="1043">40 to 180 ms</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1120" width="1520" height="60" rx="12" fill="#207448"/>
    <!-- Icon: Key / Check (white 40px) -->
    <g transform="translate(65, 1128)" fill="none" stroke="#ffffff" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="22" r="10"/>
      <line x1="26" y1="22" x2="42" y2="22"/>
      <line x1="34" y1="22" x2="34" y2="28"/>
      <line x1="40" y1="22" x2="40" y2="28"/>
    </g>
    <text x="125" y="1159" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Break latency into parts, and find the part that grows</text>
  </g>
</svg>
"""

with open("test_output.svg", "w") as f:
    f.write(svg_content)

print("Saved test_output.svg successfully")
