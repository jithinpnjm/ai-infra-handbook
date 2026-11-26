import os
import re

def build_svg_v4():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1100" width="1600" height="1100">
  <title>How parallel A and AAAA queries race in conntrack and cause a 5-second stall</title>
  <desc>Visual explanation of how parallel A and AAAA DNS queries sent from one UDP socket race during conntrack insertion and kube-proxy DNAT in Kubernetes, causing packet drops and 5-second stalls, with three resolution paths.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 14 14" refX="12" refY="7" markerWidth="14" markerHeight="14" orient="auto-start-reverse">
      <path d="M 1 2 L 12 7 L 1 12 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1100" fill="#f5f8f5" />

  <!-- Title (48px bold, at most two lines, well inside canvas) -->
  <text x="800" y="88" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">How parallel A and AAAA queries race in conntrack</tspan>
    <tspan x="800" dy="56">and cause a 5-second stall</tspan>
  </text>

  <!-- ======================================================== -->
  <!-- ROW 1: MAIN FLOW (y = 180 to y = 710)                    -->
  <!-- ======================================================== -->

  <!-- Left Container: pod (x = 50, y = 180, w = 290, h = 530) -->
  <rect id="box-pod" x="50" y="180" width="290" height="530" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Pod Header: Window Icon + Title "pod" -->
  <g transform="translate(68, 195)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="6" width="52" height="44" rx="5" />
    <line x1="2" y1="18" x2="54" y2="18" />
    <circle cx="10" cy="12" r="2" fill="#207448" />
    <circle cx="18" cy="12" r="2" fill="#207448" />
    <circle cx="26" cy="12" r="2" fill="#207448" />
  </g>
  <text x="138" y="235" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">pod</text>

  <!-- Resolver Box inside Pod: glibc resolver (x = 65, y = 255, w = 260, h = 235) -->
  <rect id="box-resolver" x="65" y="255" width="260" height="235" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <text x="195" y="295" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">glibc resolver</text>

  <!-- Sub-box inside glibc resolver: one UDP socket (x = 75, y = 315, w = 240, h = 64) -->
  <rect id="box-socket" x="75" y="315" width="240" height="64" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  <text x="195" y="354" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">one UDP socket</text>

  <!-- Note inside glibc resolver: both to the same source IP and port -->
  <text x="195" y="412" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="195" dy="0">both to the</tspan>
    <tspan x="195" dy="28">same source</tspan>
    <tspan x="195" dy="28">IP and port</tspan>
  </text>

  <!-- Step 4 on the pod side: Clock Icon + Step Circle 4 + waits for default 5 s timeout, then retries -->
  <rect id="box-step4" x="65" y="505" width="260" height="190" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Step circle 4 -->
  <circle cx="95" cy="538" r="22" fill="#207448" />
  <text x="95" y="546" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
  <!-- Clock Icon (44px) -->
  <g transform="translate(125, 518)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round">
    <circle cx="20" cy="20" r="18" />
    <polyline points="20,10 20,20 28,20" />
  </g>
  <text x="195" y="598" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="195" dy="0">waits for default</tspan>
    <tspan x="195" dy="30">5 s timeout,</tspan>
    <tspan x="195" dy="30">then retries</tspan>
  </text>

  <!-- ======================================================== -->
  <!-- TWO ARROWS LEAVING UDP SOCKET ACROSS THE 180px GAP       -->
  <!-- ======================================================== -->

  <!-- Upper arrow: A query (leaving pod at y=340, straight to netfilter at y=340) -->
  <line x1="315" y1="340" x2="518" y2="340" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="430" y="325" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">A query</text>

  <!-- Lower arrow: AAAA query (leaving pod at y=365, step down to y=520 into netfilter) -->
  <path d="M 315 365 L 360 365 Q 380 365 380 435 L 380 490 Q 380 520 410 520 L 518 520" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="430" y="505" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">AAAA query</text>

  <!-- ======================================================== -->
  <!-- STEP 1: netfilter & conntrack (x = 520, y = 180, w = 310, h = 530) -->
  <!-- ======================================================== -->
  <rect id="box-netfilter" x="520" y="180" width="310" height="530" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Step Circle 1 -->
  <circle cx="555" cy="218" r="24" fill="#207448" />
  <text x="555" y="226" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>

  <!-- CPU / Chip Icon -->
  <g transform="translate(595, 190)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="8" y="8" width="40" height="40" rx="4" />
    <rect x="18" y="18" width="20" height="20" stroke-width="3" />
    <line x1="18" y1="2" x2="18" y2="8" />
    <line x1="28" y1="2" x2="28" y2="8" />
    <line x1="38" y1="2" x2="38" y2="8" />
    <line x1="18" y1="48" x2="18" y2="54" />
    <line x1="28" y1="48" x2="28" y2="54" />
    <line x1="38" y1="48" x2="38" y2="54" />
  </g>
  <text x="665" y="228" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">netfilter</text>

  <!-- conntrack card inside netfilter (x = 535, y = 260, w = 280, h = 435) -->
  <rect id="box-conntrack" x="535" y="260" width="280" height="435" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <text x="675" y="306" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">conntrack</text>

  <!-- Note: two side-by-side insertion slots -->
  <text x="675" y="352" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="675" dy="0">two side-by-side</tspan>
    <tspan x="675" dy="32">insertion slots</tspan>
  </text>

  <!-- Two visual slots side-by-side inside conntrack -->
  <!-- Slot 1 (for A query) -->
  <rect id="slot-1" x="548" y="405" width="120" height="265" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  <!-- Slot 2 (for AAAA query) -->
  <rect id="slot-2" x="682" y="405" width="120" height="265" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />

  <!-- Flow lines inside conntrack slots -->
  <line x1="520" y1="435" x2="828" y2="435" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <line x1="520" y1="575" x2="828" y2="575" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ======================================================== -->
  <!-- STEP 2: kube-proxy DNAT (x = 870, y = 180, w = 330, h = 530) -->
  <!-- ======================================================== -->
  <rect id="box-dnat-outer" x="870" y="180" width="330" height="530" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Step Circle 2 -->
  <circle cx="905" cy="218" r="24" fill="#207448" />
  <text x="905" y="226" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>

  <!-- Gear / Service Icon -->
  <g transform="translate(945, 190)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="28" cy="28" r="12" />
    <path d="M 28 8 L 28 14 M 28 42 L 28 48 M 8 28 L 14 28 M 42 28 L 48 28 M 14 14 L 18 18 M 38 38 L 42 42 M 14 42 L 18 38 M 38 18 L 42 14" />
  </g>

  <!-- Card labelled kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC (x = 885, y = 260, w = 300, h = 435) -->
  <rect id="box-dnat-card" x="885" y="260" width="300" height="435" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  
  <text x="1035" y="302" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="1035" dy="0">kube-proxy DNAT to a</tspan>
    <tspan x="1035" dy="32">CoreDNS pod chosen</tspan>
    <tspan x="1035" dy="32">by KUBE-SVC</tspan>
  </text>

  <!-- Note: the two packets may go to different CoreDNS pods -->
  <rect id="box-dnat-note" x="898" y="445" width="274" height="225" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  <text x="1035" y="520" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1035" dy="0">the two packets may</tspan>
    <tspan x="1035" dy="34">go to different</tspan>
    <tspan x="1035" dy="34">CoreDNS pods</tspan>
  </text>

  <!-- Flow lines inside DNAT -->
  <line x1="870" y1="435" x2="1198" y2="435" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <line x1="870" y1="575" x2="1198" y2="575" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ======================================================== -->
  <!-- STEP 3: COLLISION & SILENT DROP (x = 1240, y = 180, w = 310, h = 530) -->
  <!-- ======================================================== -->
  <rect id="box-collision-outer" x="1240" y="180" width="310" height="530" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Step Circle 3 -->
  <circle cx="1275" cy="218" r="24" fill="#207448" />
  <text x="1275" y="226" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>

  <!-- Shield / Security Icon -->
  <g transform="translate(1315, 190)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 12 12 L 28 6 L 44 12 C 44 32 28 48 28 48 C 28 48 12 32 12 12 Z" />
  </g>

  <!-- Step 3 Card (x = 1255, y = 260, w = 280, h = 435) -->
  <rect id="box-collision-card" x="1255" y="260" width="280" height="435" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <!-- Label: the second insertion collides with the first -->
  <text x="1395" y="302" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="1395" dy="0">the second insertion</tspan>
    <tspan x="1395" dy="32">collides with the first</tspan>
  </text>

  <!-- Drop box for second insertion -->
  <rect id="box-drop" x="1268" y="445" width="254" height="225" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />

  <!-- Label: insert_failed -->
  <text x="1395" y="550" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">insert_failed</text>

  <!-- Label: the packet is silently dropped -->
  <text x="1395" y="600" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1395" dy="0">the packet is</tspan>
    <tspan x="1395" dy="32">silently dropped</tspan>
  </text>

  <!-- Upper arrow exits Step 3 successfully -->
  <line x1="1200" y1="435" x2="1518" y2="435" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Lower arrow enters Step 3 and ends at collision X -->
  <line x1="1200" y1="575" x2="1295" y2="575" stroke="#207448" stroke-width="3.5" />

  <!-- COLLISION X (RED-ORANGE ONLY ON THIS ELEMENT) -->
  <g stroke="#db8129" stroke-width="6" stroke-linecap="round">
    <line x1="1280" y1="490" x2="1310" y2="520" />
    <line x1="1310" y1="490" x2="1280" y2="520" />
  </g>

  <!-- ======================================================== -->
  <!-- ROW 2: GREEN FIX PATH (y = 750 to y = 910, h = 160)      -->
  <!-- ======================================================== -->

  <!-- Box 1: NodeLocal DNSCache removes the DNAT with a NOTRACK note -->
  <rect id="box-fix-1" x="50" y="750" width="470" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <!-- Outline Icon: Shield / Cache (centered horizontally in box at x=215) -->
  <g transform="translate(68, 792)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 4 8 L 22 2 L 40 8 C 40 24 22 36 22 36 C 22 36 4 24 4 8 Z" />
  </g>
  <text x="300" y="818" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="300" dy="0" font-weight="bold" fill="#207448">NodeLocal DNSCache removes</tspan>
    <tspan x="300" dy="34">the DNAT with a NOTRACK note</tspan>
  </text>

  <!-- Box 2: single-request-reopen separates the two queries -->
  <rect id="box-fix-2" x="565" y="750" width="470" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <!-- Outline Icon: Split Paths -->
  <g transform="translate(585, 792)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="10" cy="20" r="4" />
    <path d="M 14 20 L 26 10 L 38 10 M 26 10 L 32 4 M 26 30 L 38 30 M 14 20 L 26 30" />
  </g>
  <text x="815" y="818" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="815" dy="0" font-family="monospace" font-weight="bold" fill="#207448">single-request-reopen</tspan>
    <tspan x="815" dy="34">separates the two queries</tspan>
  </text>

  <!-- Box 3: TCP to DNS avoids the UDP path -->
  <rect id="box-fix-3" x="1080" y="750" width="470" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <!-- Outline Icon: TCP Handshake / Connection -->
  <g transform="translate(1098, 792)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="16" height="28" rx="2" />
    <rect x="24" y="6" width="16" height="28" rx="2" />
    <line x1="8" y1="20" x2="36" y2="20" />
  </g>
  <text x="1330" y="818" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1330" dy="0" font-weight="bold" fill="#207448">TCP to DNS avoids</tspan>
    <tspan x="1330" dy="34">the UDP path</tspan>
  </text>

  <!-- ======================================================== -->
  <!-- ROW 3: TAKEAWAY BAR (y = 950 to y = 1045, h = 95)        -->
  <!-- ======================================================== -->
  <rect id="box-takeaway" x="50" y="950" width="1500" height="95" rx="16" fill="#207448" />
  <text x="800" y="1008" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
    two parallel queries on one socket can collide in the kernel, and the lost packet costs a timeout
  </text>

</svg>'''
    return svg

with open("test_candidate_dns.svg", "w") as f:
    f.write(build_svg_v4())

print("Built test_candidate_dns.svg (v4)")
