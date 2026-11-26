import re
import xml.etree.ElementTree as ET

svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1180" width="1600" height="1180">
  <title>Socket buffers: what to raise, what to leave alone, and why</title>
  <desc>Visual infographic explaining socket buffers, autotuning, sysctl knobs, tuning recommendations, pitfalls to avoid, and BDP scaling.</desc>

  <rect width="1600" height="1180" fill="#f5f8f5"/>

  <!-- Title (wrapped onto 2 lines, font-size 48 bold) -->
  <text x="800" y="52" text-anchor="middle" font-size="48" font-weight="bold" fill="#207448" font-family="sans-serif">
    <tspan x="800" dy="0">Socket buffers: what to raise,</tspan>
    <tspan x="800" dy="54">what to leave alone, and why</tspan>
  </text>

  <!-- Left: Pipe Drawing Panel -->
  <g id="left-pipe-panel">
    <rect x="30" y="125" width="370" height="675" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    
    <!-- Pipe icon -->
    <g transform="translate(215, 155)">
      <path d="M -24 -12 L 24 -12 A 8 8 0 0 1 24 12 L -24 12 A 8 8 0 0 1 -24 -12 Z" fill="none" stroke="#207448" stroke-width="4"/>
      <ellipse cx="-24" cy="0" rx="6" ry="12" fill="none" stroke="#207448" stroke-width="4"/>
      <ellipse cx="24" cy="0" rx="6" ry="12" fill="none" stroke="#207448" stroke-width="4"/>
      <line x1="-8" y1="-12" x2="-8" y2="12" stroke="#207448" stroke-width="3" stroke-dasharray="3 3"/>
      <line x1="8" y1="-12" x2="8" y2="12" stroke="#207448" stroke-width="3" stroke-dasharray="3 3"/>
    </g>

    <!-- Send Buffer Pipe Section -->
    <g transform="translate(50, 185)">
      <rect x="0" y="0" width="330" height="185" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Pipe illustration graphic -->
      <path d="M 25 28 L 270 28 L 290 48 L 270 68 L 25 68 Z" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
      <rect x="55" y="34" width="36" height="28" rx="4" fill="#207448" opacity="0.3"/>
      <rect x="101" y="34" width="36" height="28" rx="4" fill="#207448" opacity="0.5"/>
      <rect x="147" y="34" width="36" height="28" rx="4" fill="#207448" opacity="0.8"/>
      <rect x="193" y="34" width="36" height="28" rx="4" fill="#207448"/>
      <text x="165" y="105" text-anchor="middle" font-size="24" fill="#303a36" font-family="sans-serif">
        <tspan x="165" dy="0" font-weight="bold">send buffer:</tspan>
        <tspan x="165" dy="32">unacknowledged data</tspan>
        <tspan x="165" dy="32">on the send side</tspan>
      </text>
    </g>

    <!-- Autotuning bracket / badge -->
    <g transform="translate(50, 390)">
      <rect x="0" y="0" width="330" height="95" rx="10" fill="#ffffff" stroke="#207448" stroke-width="3" stroke-dasharray="6 4"/>
      <path d="M 165 10 L 165 -18" stroke="#207448" stroke-width="3"/>
      <path d="M 165 85 L 165 115" stroke="#207448" stroke-width="3"/>
      <text x="165" y="42" text-anchor="middle" font-size="24" font-weight="bold" fill="#207448" font-family="sans-serif">
        <tspan x="165" dy="0">Linux autotunes both</tspan>
        <tspan x="165" dy="32">within limits</tspan>
      </text>
    </g>

    <!-- Receive Buffer Pipe Section -->
    <g transform="translate(50, 505)">
      <rect x="0" y="0" width="330" height="185" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      <!-- Pipe illustration graphic -->
      <path d="M 40 28 L 285 28 L 305 48 L 285 68 L 40 68 Z" fill="#e8f1ea" stroke="#207448" stroke-width="3"/>
      <rect x="65" y="34" width="36" height="28" rx="4" fill="#207448"/>
      <rect x="111" y="34" width="36" height="28" rx="4" fill="#207448" opacity="0.8"/>
      <rect x="157" y="34" width="36" height="28" rx="4" fill="#207448" opacity="0.5"/>
      <rect x="203" y="34" width="36" height="28" rx="4" fill="#207448" opacity="0.3"/>
      <text x="165" y="105" text-anchor="middle" font-size="24" fill="#303a36" font-family="sans-serif">
        <tspan x="165" dy="0" font-weight="bold">receive buffer:</tspan>
        <tspan x="165" dy="32">data the application</tspan>
        <tspan x="165" dy="32">has not read yet</tspan>
      </text>
    </g>
  </g>

  <!-- Middle: Table of Knobs -->
  <g id="middle-table-panel">
    <rect x="420" y="125" width="450" height="675" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    
    <!-- Gear icon -->
    <g transform="translate(645, 155)">
      <circle cx="0" cy="0" r="14" fill="none" stroke="#207448" stroke-width="4"/>
      <path d="M -4 -22 L 4 -22 L 3 -15 L -3 -15 Z M -4 22 L 4 22 L 3 15 L -3 15 Z M -22 -4 L -22 4 L -15 3 L -15 -3 Z M 22 -4 L 22 4 L 15 3 L 15 -3 Z M -16 -16 L -10 -10 M 16 16 L 10 10 M -16 16 L -10 10 M 16 -16 L 10 -10" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
    </g>

    <!-- Knob 1 -->
    <rect x="435" y="185" width="420" height="125" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="448" y="213" font-size="24" fill="#303a36" font-family="sans-serif">
      <tspan x="448" dy="0" font-family="monospace" font-weight="bold">net.ipv4.tcp_rmem</tspan>
      <tspan x="448" dy="26" font-family="monospace" font-weight="bold">and tcp_wmem:</tspan>
      <tspan x="448" dy="26">min default max in bytes,</tspan>
      <tspan x="448" dy="26">for example</tspan>
      <tspan x="448" dy="26" font-family="monospace">4096 131072 6291456</tspan>
    </text>

    <!-- Knob 2 -->
    <rect x="435" y="320" width="420" height="115" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="448" y="350" font-size="24" fill="#303a36" font-family="sans-serif">
      <tspan x="448" dy="0" font-family="monospace" font-weight="bold">net.core.rmem_max</tspan>
      <tspan x="448" dy="28" font-family="monospace" font-weight="bold">and wmem_max:</tspan>
      <tspan x="448" dy="28">cap for explicit SO_RCVBUF</tspan>
      <tspan x="448" dy="28">and SO_SNDBUF</tspan>
    </text>

    <!-- Knob 3 -->
    <rect x="435" y="445" width="420" height="85" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="448" y="475" font-size="24" fill="#303a36" font-family="sans-serif">
      <tspan x="448" dy="0" font-family="monospace" font-weight="bold">net.ipv4.tcp_mem:</tspan>
      <tspan x="448" dy="28">system-wide pages, low,</tspan>
      <tspan x="448" dy="28">pressure, high</tspan>
    </text>

    <!-- Knob 4 -->
    <rect x="435" y="540" width="420" height="75" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="448" y="570" font-size="24" fill="#303a36" font-family="sans-serif">
      <tspan x="448" dy="0" font-family="monospace" font-weight="bold">tcp_moderate_rcvbuf:</tspan>
      <tspan x="448" dy="28">receive autotuning (1)</tspan>
    </text>

    <!-- Knob 5 -->
    <rect x="435" y="625" width="420" height="160" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>
    <text x="448" y="652" font-size="24" fill="#303a36" font-family="sans-serif">
      <tspan x="448" dy="0" font-family="monospace" font-weight="bold">tcp_notsent_lowat:</tspan>
      <tspan x="448" dy="26">limit unsent data queued in</tspan>
      <tspan x="448" dy="26">the send buffer, reduces</tspan>
      <tspan x="448" dy="26">latency and bufferbloat,</tspan>
      <tspan x="448" dy="26">for example</tspan>
      <tspan x="448" dy="26" font-family="monospace">131072</tspan>
    </text>
  </g>

  <!-- Right: Two Columns Panel -->
  <g id="right-columns-panel">
    <!-- Outer background -->
    <rect x="890" y="125" width="680" height="675" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>

    <!-- Column 1: For 10 to 100 Gb/s long paths raise the maxima -->
    <g transform="translate(905, 140)">
      <rect x="0" y="0" width="320" height="645" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
      
      <!-- Icon: Gauge / speedometer -->
      <g transform="translate(160, 34)">
        <path d="M -22 14 A 24 24 0 1 1 22 14" fill="none" stroke="#207448" stroke-width="4"/>
        <line x1="0" y1="4" x2="14" y2="-12" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
        <circle cx="0" cy="4" r="4" fill="#207448"/>
      </g>

      <!-- Col 1 Header -->
      <text x="160" y="98" text-anchor="middle" font-size="24" font-weight="bold" fill="#207448" font-family="sans-serif">
        <tspan x="160" dy="0">For 10 to 100 Gb/s</tspan>
        <tspan x="160" dy="30">long paths raise</tspan>
        <tspan x="160" dy="30">the maxima</tspan>
      </text>

      <!-- Recommendation 1 -->
      <rect x="15" y="195" width="290" height="120" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <text x="160" y="238" text-anchor="middle" font-size="24" fill="#303a36" font-family="monospace">
        <tspan x="160" dy="0" font-weight="bold">tcp_rmem</tspan>
        <tspan x="160" dy="32">4096 131072</tspan>
        <tspan x="160" dy="32">134217728</tspan>
      </text>

      <!-- Recommendation 2 -->
      <rect x="15" y="335" width="290" height="120" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <text x="160" y="378" text-anchor="middle" font-size="24" fill="#303a36" font-family="monospace">
        <tspan x="160" dy="0" font-weight="bold">tcp_wmem</tspan>
        <tspan x="160" dy="32">4096 65536</tspan>
        <tspan x="160" dy="32">134217728</tspan>
      </text>

      <!-- Recommendation 3 -->
      <rect x="15" y="475" width="290" height="145" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
      <text x="160" y="525" text-anchor="middle" font-size="24" fill="#303a36" font-family="monospace">
        <tspan x="160" dy="0" font-weight="bold">rmem_max =</tspan>
        <tspan x="160" dy="32" font-weight="bold">wmem_max =</tspan>
        <tspan x="160" dy="32">134217728</tspan>
      </text>
    </g>

    <!-- Column 2: Do not (orange) -->
    <g transform="translate(1235, 140)">
      <rect x="0" y="0" width="320" height="645" rx="10" fill="#fff9f2" stroke="#db8129" stroke-width="3"/>
      
      <!-- Icon: Shield / Warning Octagon in orange -->
      <g transform="translate(160, 34)" stroke="#db8129" stroke-width="4">
        <polygon points="-8,-20 8,-20 20,-8 20,8 8,20 -8,20 -20,8 -20,-8" fill="none"/>
        <line x1="-8" y1="-8" x2="8" y2="8" stroke-linecap="round"/>
        <line x1="8" y1="-8" x2="-8" y2="8" stroke-linecap="round"/>
      </g>

      <!-- Col 2 Header: Do not -->
      <text x="160" y="98" text-anchor="middle" font-size="32" font-weight="bold" fill="#db8129" font-family="sans-serif">Do not</text>

      <!-- Pitfall 1 -->
      <rect x="10" y="115" width="300" height="175" rx="8" fill="#ffffff" stroke="#e0c8b0" stroke-width="1.5"/>
      <text x="22" y="140" font-size="24" fill="#303a36" font-family="sans-serif">
        <tspan x="22" dy="0">setting SO_RCVBUF</tspan>
        <tspan x="22" dy="25">or SO_SNDBUF</tspan>
        <tspan x="22" dy="25">in an application</tspan>
        <tspan x="22" dy="25">disables autotuning</tspan>
        <tspan x="22" dy="25">for that socket,</tspan>
        <tspan x="22" dy="25">almost always</tspan>
        <tspan x="22" dy="25">a mistake</tspan>
      </text>

      <!-- Pitfall 2 -->
      <rect x="10" y="300" width="300" height="160" rx="8" fill="#ffffff" stroke="#e0c8b0" stroke-width="1.5"/>
      <text x="22" y="328" font-size="24" fill="#303a36" font-family="sans-serif">
        <tspan x="22" dy="0">huge buffers on</tspan>
        <tspan x="22" dy="26">short-RTT paths</tspan>
        <tspan x="22" dy="26">add memory</tspan>
        <tspan x="22" dy="26">pressure and</tspan>
        <tspan x="22" dy="26">queueing delay:</tspan>
        <tspan x="22" dy="26">bufferbloat</tspan>
      </text>

      <!-- Pitfall 3 -->
      <rect x="10" y="470" width="300" height="165" rx="8" fill="#ffffff" stroke="#e0c8b0" stroke-width="1.5"/>
      <text x="22" y="498" font-size="24" fill="#303a36" font-family="sans-serif">
        <tspan x="22" dy="0">a 128 MB buffer on</tspan>
        <tspan x="22" dy="26">each of thousands</tspan>
        <tspan x="22" dy="26">of connections</tspan>
        <tspan x="22" dy="26">exhausts RAM;</tspan>
        <tspan x="22" dy="26">tcp_mem guards</tspan>
        <tspan x="22" dy="26">against it</tspan>
      </text>
    </g>
  </g>

  <!-- BDP Strip -->
  <g id="bdp-strip">
    <rect x="30" y="815" width="1540" height="205" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
    
    <!-- Path scale icon -->
    <g transform="translate(85, 917)">
      <circle cx="0" cy="0" r="22" fill="none" stroke="#207448" stroke-width="4"/>
      <line x1="-15" y1="0" x2="15" y2="0" stroke="#207448" stroke-width="3"/>
      <line x1="0" y1="-15" x2="0" y2="15" stroke="#207448" stroke-width="3"/>
      <circle cx="0" cy="0" r="6" fill="#207448"/>
    </g>

    <!-- Visual progression bar representing BDP tiers -->
    <g transform="translate(130, 835)">
      <rect x="0" y="0" width="270" height="14" rx="4" fill="#207448" opacity="0.3"/>
      <rect x="280" y="0" width="270" height="14" rx="4" fill="#207448" opacity="0.45"/>
      <rect x="560" y="0" width="270" height="14" rx="4" fill="#207448" opacity="0.65"/>
      <rect x="840" y="0" width="270" height="14" rx="4" fill="#207448" opacity="0.85"/>
      <rect x="1120" y="0" width="290" height="14" rx="4" fill="#207448"/>
    </g>

    <text x="130" y="880" font-size="24" fill="#303a36" font-family="sans-serif">
      <tspan x="130" dy="0">Same rack 100 Gb/s 20 microseconds: 250 KB;</tspan>
      <tspan x="130" dy="32">Same DC 100 Gb/s 100 microseconds: 1.25 MB;</tspan>
      <tspan x="130" dy="32">Metro 10 Gb/s 2 ms: 2.5 MB; Cross-continent 10 Gb/s 70 ms: 87.5 MB;</tspan>
      <tspan x="130" dy="32">Intercontinental 10 Gb/s 180 ms: 225 MB</tspan>
    </text>
  </g>

  <!-- Bottom Bar: Takeaway -->
  <g id="bottom-bar">
    <rect x="30" y="1040" width="1540" height="100" rx="12" fill="#207448"/>
    <text x="800" y="1101" text-anchor="middle" font-size="30" font-weight="bold" fill="#ffffff" font-family="sans-serif">Choose buffer sizes from the BDP of the path you use, and leave autotuning on</text>
  </g>
</svg>"""

with open("test_candidate.svg", "w") as f:
    f.write(svg_code)

print("Saved updated test_candidate.svg")
