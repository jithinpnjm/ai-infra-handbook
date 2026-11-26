import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>What QUIC fixes compared with TCP plus TLS</title>
  <desc>A comparison table contrasting TCP plus TLS with QUIC across execution layer, setup latency, head-of-line blocking, connection identity, encryption, and congestion control, with costs and AI infrastructure context.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="52" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#207448">What QUIC fixes compared with TCP plus TLS</text>

  <!-- Table Column Headers -->
  <rect x="396" y="78" width="560" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="676" y="111" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">TCP + TLS</text>

  <rect x="972" y="78" width="588" height="46" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="1266" y="111" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">QUIC (RFC 9000, under HTTP/3)</text>

  <!-- ROW 1: Where it runs -->
  <rect x="40" y="132" width="340" height="114" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" fill="none">
    <rect x="54" y="167" width="44" height="44" rx="6" stroke-width="3.5"/>
    <rect x="64" y="177" width="24" height="24" rx="2" stroke-width="2.5"/>
    <line x1="62" y1="161" x2="62" y2="167" stroke-width="3" stroke-linecap="round"/>
    <line x1="76" y1="161" x2="76" y2="167" stroke-width="3" stroke-linecap="round"/>
    <line x1="90" y1="161" x2="90" y2="167" stroke-width="3" stroke-linecap="round"/>
    <line x1="62" y1="211" x2="62" y2="217" stroke-width="3" stroke-linecap="round"/>
    <line x1="76" y1="211" x2="76" y2="217" stroke-width="3" stroke-linecap="round"/>
    <line x1="90" y1="211" x2="90" y2="217" stroke-width="3" stroke-linecap="round"/>
    <line x1="48" y1="175" x2="54" y2="175" stroke-width="3" stroke-linecap="round"/>
    <line x1="48" y1="189" x2="54" y2="189" stroke-width="3" stroke-linecap="round"/>
    <line x1="48" y1="203" x2="54" y2="203" stroke-width="3" stroke-linecap="round"/>
    <line x1="98" y1="175" x2="104" y2="175" stroke-width="3" stroke-linecap="round"/>
    <line x1="98" y1="189" x2="104" y2="189" stroke-width="3" stroke-linecap="round"/>
    <line x1="98" y1="203" x2="104" y2="203" stroke-width="3" stroke-linecap="round"/>
  </g>
  <text x="118" y="181" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="118" dy="0">Where</tspan>
    <tspan x="118" dy="34">it runs</tspan>
  </text>

  <rect x="396" y="132" width="560" height="114" rx="10" fill="#ffffff" stroke="#c8dcd0" stroke-width="2"/>
  <text x="424" y="198" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">kernel</text>

  <rect x="972" y="132" width="588" height="114" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="998" y="171" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="998" dy="0">over UDP, in user space, so changing</tspan>
    <tspan x="998" dy="30">a library is far easier than changing</tspan>
    <tspan x="998" dy="30">every operating system</tspan>
  </text>

  <!-- ROW 2: Setup cost -->
  <rect x="40" y="254" width="340" height="136" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" fill="none">
    <circle cx="76" cy="322" r="22" stroke-width="3.5"/>
    <polyline points="76,308 76,322 89,322" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
  </g>
  <text x="118" y="309" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="118" dy="0">Setup</tspan>
    <tspan x="118" dy="34">cost</tspan>
  </text>

  <rect x="396" y="254" width="560" height="136" rx="10" fill="#ffffff" stroke="#c8dcd0" stroke-width="2"/>
  <text x="424" y="316" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="424" dy="0">transport handshake then TLS,</tspan>
    <tspan x="424" dy="32">2 to 3 RTTs</tspan>
  </text>

  <rect x="972" y="254" width="588" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="998" y="291" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="998" dy="0">transport and TLS 1.3 combined,</tspan>
    <tspan x="998" dy="28">1 RTT for a new connection,</tspan>
    <tspan x="998" dy="28">0-RTT data on resumption which</tspan>
    <tspan x="998" dy="28">must be safe to replay</tspan>
  </text>

  <!-- ROW 3: Head-of-line blocking -->
  <rect x="40" y="398" width="340" height="114" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" stroke-linecap="round">
    <line x1="56" y1="441" x2="96" y2="441" stroke-width="3.5"/>
    <line x1="56" y1="455" x2="96" y2="455" stroke-width="3.5"/>
    <line x1="56" y1="469" x2="96" y2="469" stroke-width="3.5"/>
    <line x1="84" y1="433" x2="84" y2="477" stroke-width="4"/>
  </g>
  <text x="118" y="447" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="118" dy="0">Head-of-line</tspan>
    <tspan x="118" dy="34">blocking</tspan>
  </text>

  <!-- Orange highlight on the single most important item -->
  <rect x="396" y="398" width="560" height="114" rx="10" fill="#fff8f0" stroke="#db8129" stroke-width="3"/>
  <text x="424" y="449" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#db8129">
    <tspan x="424" dy="0">one loss stalls every stream</tspan>
    <tspan x="424" dy="30">on the connection</tspan>
  </text>

  <rect x="972" y="398" width="588" height="114" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="998" y="441" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="998" dy="0">streams are independent lanes;</tspan>
    <tspan x="998" dy="30">a loss stalls only the stream</tspan>
    <tspan x="998" dy="30">or streams it carried</tspan>
  </text>

  <!-- ROW 4: Connection identity -->
  <rect x="40" y="520" width="340" height="114" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" fill="none">
    <rect x="54" y="560" width="46" height="34" rx="4" stroke-width="3.5"/>
    <circle cx="68" cy="574" r="5" stroke-width="2.5"/>
    <line x1="78" y1="571" x2="92" y2="571" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="78" y1="579" x2="90" y2="579" stroke-width="2.5" stroke-linecap="round"/>
  </g>
  <text x="118" y="569" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="118" dy="0">Connection</tspan>
    <tspan x="118" dy="34">identity</tspan>
  </text>

  <rect x="396" y="520" width="560" height="114" rx="10" fill="#ffffff" stroke="#c8dcd0" stroke-width="2"/>
  <text x="424" y="571" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="424" dy="0">4-tuple, a change of IP</tspan>
    <tspan x="424" dy="30">breaks it</tspan>
  </text>

  <rect x="972" y="520" width="588" height="114" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="998" y="563" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="998" dy="0">connection IDs let a connection</tspan>
    <tspan x="998" dy="30">survive a change of IP address,</tspan>
    <tspan x="998" dy="30">such as Wi-Fi to cellular</tspan>
  </text>

  <!-- ROW 5: Encryption -->
  <rect x="40" y="642" width="340" height="114" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" fill="none">
    <rect x="60" y="689" width="32" height="24" rx="4" stroke-width="3.5"/>
    <path d="M66,689 V680 A10,10 0 0,1 86,680 V689" stroke-width="3.5"/>
    <circle cx="76" cy="700" r="2.5" fill="#207448"/>
    <line x1="76" y1="702" x2="76" y2="707" stroke-width="2.5"/>
  </g>
  <text x="118" y="710" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">Encryption</text>

  <rect x="396" y="642" width="560" height="114" rx="10" fill="#ffffff" stroke="#c8dcd0" stroke-width="2"/>
  <text x="424" y="708" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">optional TLS on top</text>

  <rect x="972" y="642" width="588" height="114" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="998" y="685" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="998" dy="0">mandatory, covers most of the</tspan>
    <tspan x="998" dy="30">transport header, so middleboxes</tspan>
    <tspan x="998" dy="30">cannot meddle or optimise</tspan>
  </text>

  <!-- ROW 6: Congestion control -->
  <rect x="40" y="764" width="340" height="136" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" fill="none">
    <path d="M56,842 A22,22 0 1,1 96,842" stroke-width="3.5" stroke-linecap="round"/>
    <line x1="76" y1="832" x2="88" y2="820" stroke-width="3.5" stroke-linecap="round"/>
    <circle cx="76" cy="832" r="3" fill="#207448"/>
  </g>
  <text x="118" y="819" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="118" dy="0">Congestion</tspan>
    <tspan x="118" dy="34">control</tspan>
  </text>

  <rect x="396" y="764" width="560" height="136" rx="10" fill="#ffffff" stroke="#c8dcd0" stroke-width="2"/>
  <text x="424" y="840" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">kernel choice</text>

  <rect x="972" y="764" width="588" height="136" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="998" y="801" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="998" dy="0">each application picks its own,</tspan>
    <tspan x="998" dy="28">such as CUBIC or BBR; monotonic</tspan>
    <tspan x="998" dy="28">packet numbers avoid retransmission</tspan>
    <tspan x="998" dy="28">ambiguity; ACK ranges</tspan>
  </text>

  <!-- COSTS ROW BELOW -->
  <rect x="40" y="910" width="1520" height="114" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" fill="none">
    <path d="M76,938 L98,978 L54,978 Z" stroke-width="3.5" stroke-linejoin="round"/>
    <line x1="76" y1="952" x2="76" y2="964" stroke-width="3" stroke-linecap="round"/>
    <circle cx="76" cy="971" r="1.8" fill="#207448"/>
  </g>
  <text x="118" y="949" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="118" dy="0">more CPU because crypto and packetisation run in user space (UDP GSO helps),</tspan>
    <tspan x="118" dy="29">some networks block or rate-limit UDP, harder to observe: encrypted headers limit</tspan>
    <tspan x="118" dy="29">what you can see, use qlog and endpoint metrics</tspan>
  </text>

  <!-- FOOTER -->
  <rect x="40" y="1034" width="1520" height="80" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <g stroke="#207448" fill="none">
    <circle cx="76" cy="1074" r="18" stroke-width="3"/>
    <ellipse cx="76" cy="1074" rx="8" ry="18" stroke-width="2.5"/>
    <line x1="58" y1="1074" x2="94" y2="1074" stroke-width="2.5"/>
  </g>
  <text x="118" y="1068" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="118" dy="0">In AI infrastructure QUIC mostly appears at the edge, such as HTTP/3 to inference APIs</tspan>
    <tspan x="118" dy="30">and CDNs, rather than inside clusters</tspan>
  </text>

  <!-- BOTTOM BAR -->
  <rect x="40" y="1124" width="1520" height="52" rx="8" fill="#207448"/>
  <text x="800" y="1159" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">ICMP, with ping, traceroute and PMTUD, is covered in chapter 2.7</text>
</svg>"""

with open("test_out.svg", "w") as f:
    f.write(svg_content)
print("Saved test_out.svg")
