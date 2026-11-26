import xml.etree.ElementTree as ET
import re

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>The twelve lab steps, from a healthy trace to the faults</title>
  <desc>Visual infographic ladder of twelve lab steps in three groups: reading a healthy trace, injecting faults and comparing, and using wider diagnostic tools.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="50" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The twelve lab steps, from a healthy trace to the faults</text>

  <!-- ==================== PRE-STEP BANNER ==================== -->
  <g id="pre-step">
    <rect x="40" y="74" width="1520" height="66" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <!-- Outline icon: terminal / script check (56px) -->
    <g transform="translate(56, 79)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="44" rx="6" />
      <polyline points="14,20 24,28 14,36" />
      <line x1="28" y1="36" x2="42" y2="36" stroke-width="3.5" />
    </g>
    <text font-family="monospace" font-size="24" fill="#303a36">
      <tspan x="128" y="103">python3 code/part02/packet_capture_bpf_lab.py checks the byte-offset filters, the 8.13 Mpps rate at 100 Gb/s, </tspan>
      <tspan x="128" y="129">ring storage with -s 96, and the two-endpoint comparison</tspan>
    </text>
  </g>

  <!-- ==================== GROUP 1: Read a healthy trace (Steps 1-2) ==================== -->
  <g id="group-1">
    <rect x="40" y="152" width="1520" height="236" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Header bar -->
    <path d="M 40 168 A 16 16 0 0 1 56 152 L 1544 152 A 16 16 0 0 1 1560 168 L 1560 196 L 40 196 Z" fill="#e8f1ea" />
    <text x="60" y="184" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Read a healthy trace</text>

    <!-- Step 1 Card -->
    <rect x="60" y="208" width="710" height="164" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <!-- Number circle 1 -->
    <circle cx="96" cy="244" r="24" fill="#207448" />
    <text x="96" y="253" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    <!-- Outline icon: Handshake / TCP 3-way link (56px) -->
    <g transform="translate(132, 216)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="14" cy="28" r="8" />
      <circle cx="42" cy="28" r="8" />
      <path d="M 22 28 L 34 28" stroke-width="4" />
      <path d="M 14 20 C 14 10 42 10 42 20" stroke-width="3" />
      <path d="M 14 36 C 14 46 42 46 42 36" stroke-width="3" />
    </g>
    <!-- Step 1 Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="252" font-size="30" font-weight="bold" fill="#207448">1 Handshake and teardown: </tspan>
      <tspan x="84" y="296" font-family="monospace">curl to local nginx, label SYN, SYN-ACK, </tspan>
      <tspan x="84" y="324" font-family="monospace">ACK, FIN, export with tshark -z follow</tspan>
    </text>

    <!-- Step 2 Card -->
    <rect x="830" y="208" width="710" height="164" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <!-- Number circle 2 -->
    <circle cx="866" cy="244" r="24" fill="#207448" />
    <text x="866" y="253" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>
    <!-- Outline icon: Filter / Funnel (56px) -->
    <g transform="translate(902, 216)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="8,10 48,10 32,30 32,46 24,46 24,30" />
      <line x1="14" y1="18" x2="42" y2="18" stroke-width="3" />
    </g>
    <!-- Step 2 Text -->
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="972" y="252" font-size="30" font-weight="bold" fill="#207448">2 Filters: </tspan>
      <tspan x="854" y="284">five capture filters for SYN only, RST, </tspan>
      <tspan x="854" y="310">a port range, DSCP EF and VLAN, verified with </tspan>
      <tspan x="854" y="336" font-family="monospace">tcpdump -d <tspan font-family="sans-serif">and hit counts, then the same </tspan></tspan>
      <tspan x="854" y="360">logic as display filters</tspan>
    </text>
  </g>

  <!-- ==================== GROUP 2: Inject a fault and compare (Steps 3-7, orange) ==================== -->
  <g id="group-2">
    <rect x="40" y="400" width="740" height="725" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3" />
    <!-- Header bar in orange -->
    <path d="M 40 416 A 16 16 0 0 1 56 400 L 764 400 A 16 16 0 0 1 780 416 L 780 444 L 40 444 Z" fill="#db8129" />
    <text x="60" y="432" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Inject a fault and compare</text>

    <!-- Step 3 Card -->
    <rect x="60" y="456" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="492" r="24" fill="#db8129" />
    <text x="95" y="501" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>
    <g transform="translate(132, 464)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 10 28 C 10 14 24 10 38 14 C 48 18 48 30 38 34 L 14 34" />
      <polyline points="20,28 14,34 20,40" />
      <line x1="28" y1="44" x2="44" y2="44" stroke-dasharray="4 4" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="498" font-size="30" font-weight="bold" fill="#db8129">3 Retransmissions and loss: </tspan>
      <tspan x="84" y="534" font-family="monospace">tc qdisc add dev veth1 root netem loss 2%, </tspan>
      <tspan x="84" y="562">compare with 0% loss</tspan>
    </text>

    <!-- Step 4 Card -->
    <rect x="60" y="590" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="626" r="24" fill="#db8129" />
    <text x="95" y="635" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>
    <g transform="translate(132, 598)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="14" width="40" height="28" rx="4" />
      <line x1="28" y1="6" x2="28" y2="14" />
      <line x1="16" y1="28" x2="40" y2="28" stroke-dasharray="4 3" />
      <line x1="20" y1="42" x2="36" y2="42" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="632" font-size="30" font-weight="bold" fill="#db8129">4 MTU black hole: </tspan>
      <tspan x="84" y="668">smaller MTU on a router namespace, drop ICMP </tspan>
      <tspan x="84" y="696">type 3 code 4, then fix with MSS clamping</tspan>
    </text>

    <!-- Step 5 Card -->
    <rect x="60" y="724" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="760" r="24" fill="#db8129" />
    <text x="95" y="769" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>
    <g transform="translate(132, 732)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="4" />
      <line x1="8" y1="20" x2="48" y2="20" />
      <line x1="22" y1="30" x2="22" y2="42" stroke-width="5" />
      <line x1="34" y1="30" x2="34" y2="42" stroke-width="5" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="766" font-size="30" font-weight="bold" fill="#db8129">5 Zero window: </tspan>
      <tspan x="84" y="806">a server that sleeps before it reads</tspan>
    </text>

    <!-- Step 6 Card -->
    <rect x="60" y="858" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="894" r="24" fill="#db8129" />
    <text x="95" y="903" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">6</text>
    <g transform="translate(132, 866)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="12" y="22" width="32" height="26" rx="4" />
      <path d="M 18 22 V 14 C 18 8 38 8 38 14 V 22" />
      <circle cx="28" cy="34" r="3" fill="#db8129" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="900" font-size="30" font-weight="bold" fill="#db8129">6 TLS: </tspan>
      <tspan x="84" y="936" font-family="monospace">SSLKEYLOGFILE=/tmp/keys.log curl </tspan>
      <tspan x="84" y="964"><tspan font-family="monospace">https://localhost, </tspan>read SNI and ALPN</tspan>
    </text>

    <!-- Step 7 Card -->
    <rect x="60" y="992" width="700" height="122" rx="10" fill="#fffaf5" stroke="#db8129" stroke-width="1.5" />
    <circle cx="95" cy="1028" r="24" fill="#db8129" />
    <text x="95" y="1037" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">7</text>
    <g transform="translate(132, 1000)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="12" y="12" width="32" height="32" rx="4" />
      <line x1="8" y1="20" x2="12" y2="20" /><line x1="8" y1="28" x2="12" y2="28" /><line x1="8" y1="36" x2="12" y2="36" />
      <line x1="44" y1="20" x2="48" y2="20" /><line x1="44" y1="28" x2="48" y2="28" /><line x1="44" y1="36" x2="48" y2="36" />
      <polyline points="20,28 26,34 36,22" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="202" y="1034" font-size="30" font-weight="bold" fill="#db8129">7 Offload artefacts: </tspan>
      <tspan x="84" y="1074">TSO and checksum offload on then off</tspan>
    </text>
  </g>

  <!-- ==================== GROUP 3: Wider tools (Steps 8-12) ==================== -->
  <g id="group-3">
    <rect x="820" y="400" width="740" height="725" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Header bar -->
    <path d="M 820 416 A 16 16 0 0 1 836 400 L 1544 400 A 16 16 0 0 1 1560 416 L 1560 444 L 820 444 Z" fill="#e8f1ea" />
    <text x="840" y="432" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Wider tools</text>

    <!-- Step 8 Card -->
    <rect x="840" y="456" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="492" r="24" fill="#207448" />
    <text x="875" y="501" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">8</text>
    <g transform="translate(912, 464)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="44" height="22" rx="3" />
      <rect x="6" y="26" width="44" height="22" rx="3" fill="#e8f1ea" />
      <line x1="16" y1="19" x2="40" y2="19" stroke-width="2.5" />
      <line x1="16" y1="37" x2="40" y2="37" stroke-width="2.5" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="982" y="498" font-size="30" font-weight="bold" fill="#207448">8 Overlay: </tspan>
      <tspan x="864" y="538">VXLAN link as in chapter 2.17, Decode As</tspan>
    </text>

    <!-- Step 9 Card -->
    <rect x="840" y="590" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="626" r="24" fill="#207448" />
    <text x="875" y="635" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">9</text>
    <g transform="translate(912, 598)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="18" />
      <path d="M 28 10 A 18 18 0 0 1 46 28" stroke-dasharray="3 3" />
      <polyline points="28,20 28,28 34,34" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="982" y="632" font-size="30" font-weight="bold" fill="#207448">9 Ring buffer and trigger: </tspan>
      <tspan x="864" y="672" font-family="monospace">tcpdump -C 10 -W 5 <tspan font-family="sans-serif">plus a stop script</tspan></tspan>
    </text>

    <!-- Step 10 Card -->
    <rect x="840" y="724" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="760" r="24" fill="#207448" />
    <text x="875" y="769" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">10</text>
    <g transform="translate(912, 732)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 14 C 18 8 38 8 44 14 C 50 20 46 36 28 48 C 10 36 6 20 12 14 Z" />
      <line x1="28" y1="20" x2="28" y2="34" />
      <line x1="20" y1="26" x2="36" y2="26" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="982" y="766" font-size="30" font-weight="bold" fill="#207448">10 BPF tools: </tspan>
      <tspan x="864" y="802" font-family="monospace">tcplife, tcpconnect, tcpretrans, tcpdrop, </tspan>
      <tspan x="864" y="828">three bpftrace one-liners</tspan>
    </text>

    <!-- Step 11 Card -->
    <rect x="840" y="858" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="894" r="24" fill="#207448" />
    <text x="875" y="903" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">11</text>
    <g transform="translate(912, 866)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 16 V 38 L 28 48 L 8 38 V 16 Z" />
      <line x1="28" y1="6" x2="28" y2="48" />
      <line x1="28" y1="27" x2="48" y2="16" />
      <line x1="28" y1="27" x2="8" y2="16" />
    </g>
    <text font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="982" y="900" font-size="30" font-weight="bold" fill="#207448">11 Container capture: </tspan>
      <tspan x="864" y="936" font-family="monospace">nsenter, <tspan font-family="sans-serif">then </tspan>docker run --network </tspan>
      <tspan x="864" y="964" font-family="monospace">container:NAME nicolaka/netshoot tcpdump</tspan>
    </text>

    <!-- Step 12 Card -->
    <rect x="840" y="992" width="700" height="122" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
    <circle cx="875" cy="1028" r="24" fill="#207448" />
    <text x="875" y="1037" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">12</text>
    <g transform="translate(912, 1000)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 16 L 44 16 L 40 46 L 16 46 Z" />
      <line x1="8" y1="16" x2="48" y2="16" />
      <path d="M 22 16 V 10 C 22 8 34 8 34 10 V 16" />
      <line x1="22" y1="24" x2="22" y2="38" />
      <line x1="34" y1="24" x2="34" y2="38" />
    </g>
    <text font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="982" y="1032">12 Clean up and delete captures, </tspan>
      <tspan x="864" y="1070">key log and ring-buffer directory</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM BAR ==================== -->
  <g id="bottom-bar">
    <rect x="40" y="1138" width="1520" height="46" rx="10" fill="#207448" />
    <text x="800" y="1169" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">The healthy trace from step 1 is the reference that makes the faulty traces stand out</text>
  </g>
</svg>
'''

with open("test_lab_ladder.svg", "w") as f:
    f.write(svg_content.strip())

print("Wrote test_lab_ladder.svg successfully!")
