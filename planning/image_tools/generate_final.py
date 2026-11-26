import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>The twelve lab steps, from a healthy trace to the faults</title>
  <desc>Visual infographic ladder of twelve lab steps in three groups: reading a healthy trace, injecting faults and comparing, and using wider diagnostic tools.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold, 2 lines for generous padding) -->
  <text font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">
    <tspan x="800" y="52">The twelve lab steps, </tspan>
    <tspan x="800" y="92">from a healthy trace to the faults</tspan>
  </text>

  <!-- ==================== PRE-STEP BANNER ==================== -->
  <g id="pre-step">
    <rect x="40" y="102" width="1520" height="88" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Outline icon: terminal / script check (52px) -->
    <g transform="translate(56, 120)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="40" rx="6" />
      <polyline points="14,18 24,26 14,34" />
      <line x1="28" y1="34" x2="42" y2="34" stroke-width="3.5" />
    </g>
    <text font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="128" y="138">python3 code/part02/packet_capture_bpf_lab.py checks the byte-offset filters, </tspan>
      <tspan x="128" y="166">the 8.13 Mpps rate at 100 Gb/s, ring storage with -s 96, and the two-endpoint comparison</tspan>
    </text>
  </g>

  <!-- ==================== GROUP 1: Read a healthy trace (Steps 1-2) ==================== -->
  <g id="group-1">
    <rect x="40" y="206" width="1520" height="244" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Header bar -->
    <path d="M 40 222 A 16 16 0 0 1 56 206 L 1544 206 A 16 16 0 0 1 1560 222 L 1560 248 L 40 248 Z" fill="#e8f1ea" />
    <text x="60" y="238" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Read a healthy trace</text>

    <!-- Step 1 Card -->
    <rect x="60" y="258" width="710" height="180" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <!-- Number circle 1 -->
    <circle cx="95" cy="296" r="24" fill="#207448" />
    <text x="95" y="305" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Outline icon: Handshake / TCP 3-way link (50px) -->
    <g transform="translate(132, 272)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="12" cy="24" r="8" />
      <circle cx="38" cy="24" r="8" />
      <path d="M 20 24 L 30 24" stroke-width="4" />
      <path d="M 12 16 C 12 6 38 6 38 16" stroke-width="3" />
      <path d="M 12 32 C 12 42 38 42 38 32" stroke-width="3" />
    </g>
    <!-- Step 1 Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="300" font-size="30" font-weight="bold" fill="#207448">1 Handshake and teardown: </tspan>
      <tspan x="84" y="348" font-family="monospace">curl to local nginx, label SYN, SYN-ACK, </tspan>
      <tspan x="84" y="384" font-family="monospace">ACK, FIN, export with tshark -z follow</tspan>
    </text>

    <!-- Step 2 Card -->
    <rect x="830" y="258" width="710" height="180" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <!-- Number circle 2 -->
    <circle cx="865" cy="296" r="24" fill="#207448" />
    <text x="865" y="305" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Outline icon: Filter / Funnel (50px) -->
    <g transform="translate(902, 272)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="6,8 44,8 28,26 28,42 22,42 22,26" />
      <line x1="12" y1="16" x2="38" y2="16" stroke-width="3" />
    </g>
    <!-- Step 2 Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="972" y="300" font-size="30" font-weight="bold" fill="#207448">2 Filters: </tspan>
      <tspan x="854" y="332">five capture filters for SYN only, RST, </tspan>
      <tspan x="854" y="358">a port range, DSCP EF and VLAN, verified with </tspan>
      <tspan x="854" y="384" font-family="monospace">tcpdump -d <tspan font-family="sans-serif">and hit counts, then the same </tspan></tspan>
      <tspan x="854" y="410">logic as display filters</tspan>
    </text>
  </g>

  <!-- ==================== GROUP 2: Inject a fault and compare (Steps 3-7, orange) ==================== -->
  <g id="group-2">
    <rect x="40" y="466" width="740" height="650" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3" />
    <!-- Header bar in orange -->
    <path d="M 40 482 A 16 16 0 0 1 56 466 L 764 466 A 16 16 0 0 1 780 482 L 780 506 L 40 506 Z" fill="#db8129" />
    <text x="60" y="496" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Inject a fault and compare</text>

    <!-- Step 3 Card -->
    <rect x="60" y="516" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="552" r="24" fill="#db8129" />
    <text x="95" y="561" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <g transform="translate(132, 528)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 24 C 8 12 20 8 32 12 C 42 16 42 26 32 30 L 12 30" />
      <polyline points="18,24 12,30 18,36" />
      <line x1="24" y1="40" x2="40" y2="40" stroke-dasharray="4 4" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="556" font-size="30" font-weight="bold" fill="#db8129">3 Retransmissions and loss: </tspan>
      <tspan x="84" y="588" font-family="monospace">tc qdisc add dev veth1 root netem loss 2%, </tspan>
      <tspan x="84" y="614">compare with 0% loss</tspan>
    </text>

    <!-- Step 4 Card -->
    <rect x="60" y="638" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="674" r="24" fill="#db8129" />
    <text x="95" y="683" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <g transform="translate(132, 650)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="38" height="26" rx="4" />
      <line x1="25" y1="4" x2="25" y2="10" />
      <line x1="14" y1="23" x2="36" y2="23" stroke-dasharray="4 3" />
      <line x1="18" y1="36" x2="32" y2="36" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="678" font-size="30" font-weight="bold" fill="#db8129">4 MTU black hole: </tspan>
      <tspan x="84" y="710">smaller MTU on a router namespace, drop ICMP </tspan>
      <tspan x="84" y="736">type 3 code 4, then fix with MSS clamping</tspan>
    </text>

    <!-- Step 5 Card -->
    <rect x="60" y="760" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="796" r="24" fill="#db8129" />
    <text x="95" y="805" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>
    <g transform="translate(132, 772)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="38" height="36" rx="4" />
      <line x1="6" y1="18" x2="44" y2="18" />
      <line x1="18" y1="26" x2="18" y2="36" stroke-width="4.5" />
      <line x1="28" y1="26" x2="28" y2="36" stroke-width="4.5" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="802" font-size="30" font-weight="bold" fill="#db8129">5 Zero window: </tspan>
      <tspan x="84" y="846">a server that sleeps before it reads</tspan>
    </text>

    <!-- Step 6 Card -->
    <rect x="60" y="882" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="918" r="24" fill="#db8129" />
    <text x="95" y="927" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">6</text>
    <g transform="translate(132, 894)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="20" width="30" height="24" rx="4" />
      <path d="M 16 20 V 12 C 16 7 34 7 34 12 V 20" />
      <circle cx="25" cy="30" r="2.5" fill="#db8129" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="922" font-size="30" font-weight="bold" fill="#db8129">6 TLS: </tspan>
      <tspan x="84" y="954" font-family="monospace">SSLKEYLOGFILE=/tmp/keys.log curl </tspan>
      <tspan x="84" y="980"><tspan font-family="monospace">https://localhost, </tspan>read SNI and ALPN</tspan>
    </text>

    <!-- Step 7 Card -->
    <rect x="60" y="1004" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="1040" r="24" fill="#db8129" />
    <text x="95" y="1049" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">7</text>
    <g transform="translate(132, 1016)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="30" height="30" rx="4" />
      <line x1="6" y1="18" x2="10" y2="18" /><line x1="6" y1="26" x2="10" y2="26" /><line x1="6" y1="34" x2="10" y2="34" />
      <line x1="40" y1="18" x2="44" y2="18" /><line x1="40" y1="26" x2="44" y2="26" /><line x1="40" y1="34" x2="44" y2="34" />
      <polyline points="18,25 23,30 32,20" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="1046" font-size="30" font-weight="bold" fill="#db8129">7 Offload artefacts: </tspan>
      <tspan x="84" y="1090">TSO and checksum offload on then off</tspan>
    </text>
  </g>

  <!-- ==================== GROUP 3: Wider tools (Steps 8-12) ==================== -->
  <g id="group-3">
    <rect x="820" y="466" width="740" height="650" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Header bar -->
    <path d="M 820 482 A 16 16 0 0 1 836 466 L 1544 466 A 16 16 0 0 1 1560 482 L 1560 506 L 820 506 Z" fill="#e8f1ea" />
    <text x="840" y="496" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Wider tools</text>

    <!-- Step 8 Card -->
    <rect x="840" y="516" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="552" r="24" fill="#207448" />
    <text x="875" y="561" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">8</text>
    <g transform="translate(912, 528)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="40" height="20" rx="3" />
      <rect x="4" y="22" width="40" height="20" rx="3" fill="#e8f1ea" />
      <line x1="14" y1="16" x2="34" y2="16" stroke-width="2.5" />
      <line x1="14" y1="32" x2="34" y2="32" stroke-width="2.5" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="982" y="558" font-size="30" font-weight="bold" fill="#207448">8 Overlay: </tspan>
      <tspan x="864" y="602">VXLAN link as in chapter 2.17, Decode As</tspan>
    </text>

    <!-- Step 9 Card -->
    <rect x="840" y="638" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="674" r="24" fill="#207448" />
    <text x="875" y="683" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">9</text>
    <g transform="translate(912, 650)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="24" cy="24" r="16" />
      <path d="M 24 8 A 16 16 0 0 1 40 24" stroke-dasharray="3 3" />
      <polyline points="24,16 24,24 30,30" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="982" y="680" font-size="30" font-weight="bold" fill="#207448">9 Ring buffer and trigger: </tspan>
      <tspan x="864" y="722" font-family="monospace">tcpdump -C 10 -W 5 <tspan font-family="sans-serif">plus a stop script</tspan></tspan>
    </text>

    <!-- Step 10 Card -->
    <rect x="840" y="760" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="796" r="24" fill="#207448" />
    <text x="875" y="805" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">10</text>
    <g transform="translate(912, 772)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 12 C 16 6 34 6 40 12 C 46 18 42 32 25 44 C 8 32 4 18 10 12 Z" />
      <line x1="25" y1="18" x2="25" y2="30" />
      <line x1="18" y1="24" x2="32" y2="24" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="982" y="802" font-size="30" font-weight="bold" fill="#207448">10 BPF tools: </tspan>
      <tspan x="864" y="834" font-family="monospace">tcplife, tcpconnect, tcpretrans, tcpdrop, </tspan>
      <tspan x="864" y="860">three bpftrace one-liners</tspan>
    </text>

    <!-- Step 11 Card -->
    <rect x="840" y="882" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="918" r="24" fill="#207448" />
    <text x="875" y="927" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">11</text>
    <g transform="translate(912, 894)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 24 6 L 42 16 V 34 L 24 44 L 6 34 V 16 Z" />
      <line x1="24" y1="6" x2="24" y2="44" />
      <line x1="24" y1="24" x2="42" y2="16" />
      <line x1="24" y1="24" x2="6" y2="16" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="982" y="922" font-size="30" font-weight="bold" fill="#207448">11 Container capture: </tspan>
      <tspan x="864" y="954" font-family="monospace">nsenter, <tspan font-family="sans-serif">then </tspan>docker run --network </tspan>
      <tspan x="864" y="980" font-family="monospace">container:NAME nicolaka/netshoot tcpdump</tspan>
    </text>

    <!-- Step 12 Card -->
    <rect x="840" y="1004" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="1040" r="24" fill="#207448" />
    <text x="875" y="1049" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">12</text>
    <g transform="translate(912, 1016)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 14 L 38 14 L 34 40 L 14 40 Z" />
      <line x1="6" y1="14" x2="42" y2="14" />
      <path d="M 20 14 V 9 C 20 7 28 7 28 9 V 14" />
      <line x1="20" y1="20" x2="20" y2="34" />
      <line x1="28" y1="20" x2="28" y2="34" />
    </g>
    <text font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="982" y="1046">12 Clean up and delete captures, </tspan>
      <tspan x="864" y="1086">key log and ring-buffer directory</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1130" width="1520" height="58" rx="10" fill="#207448" />
    <text x="800" y="1165" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">The healthy trace from step 1 is the reference that makes the faulty traces stand out</text>
  </g>
</svg>'''

with open("p3_0226_lab_ladder.svg", "w") as f:
    f.write(svg_code.strip())

print("Wrote p3_0226_lab_ladder.svg successfully!")
