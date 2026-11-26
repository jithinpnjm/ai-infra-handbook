import os
import re

def build_svg():
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

  <!-- Left Container: pod (x = 50, y = 180, w = 340, h = 530) -->
  <rect id="box-pod" x="50" y="180" width="340" height="530" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Pod Header: Window Icon + Title "pod" -->
  <g transform="translate(75, 195)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="6" width="52" height="44" rx="5" />
    <line x1="2" y1="18" x2="54" y2="18" />
    <circle cx="10" cy="12" r="2" fill="#207448" />
    <circle cx="18" cy="12" r="2" fill="#207448" />
    <circle cx="26" cy="12" r="2" fill="#207448" />
  </g>
  <text x="145" y="235" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">pod</text>

  <!-- Resolver Box inside Pod: glibc resolver (x = 68, y = 260, w = 304, h = 230) -->
  <rect id="box-resolver" x="68" y="260" width="304" height="230" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <text x="220" y="300" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">glibc resolver</text>

  <!-- Sub-box inside glibc resolver: one UDP socket (x = 84, y = 320, w = 272, h = 65) -->
  <rect id="box-socket" x="84" y="320" width="272" height="65" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  <text x="220" y="362" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">one UDP socket</text>

  <!-- Note inside glibc resolver: both to the same source IP and port -->
  <text x="220" y="425" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="220" dy="0">both to the same</tspan>
    <tspan x="220" dy="32">source IP and port</tspan>
  </text>

  <!-- Step 4 on the pod side: Clock Icon + Step Circle 4 + waits for default 5 s timeout, then retries -->
  <rect id="box-step4" x="68" y="515" width="304" height="175" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <!-- Step circle 4 -->
  <circle cx="102" cy="548" r="22" fill="#207448" />
  <text x="102" y="556" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">4</text>
  <!-- Clock Icon (44px) -->
  <g transform="translate(136, 528)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round">
    <circle cx="20" cy="20" r="18" />
    <polyline points="20,10 20,20 28,20" />
  </g>
  <text x="220" y="608" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="220" dy="0">waits for default 5 s</tspan>
    <tspan x="220" dy="32">timeout, then retries</tspan>
  </text>

  <!-- ======================================================== -->
  <!-- STEP 1: netfilter & conntrack (x = 430, y = 180, w = 340, h = 530) -->
  <!-- ======================================================== -->
  <rect id="box-netfilter" x="430" y="180" width="340" height="530" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Step Circle 1 -->
  <circle cx="465" cy="218" r="24" fill="#207448" />
  <text x="465" y="226" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">1</text>

  <!-- CPU / Chip Icon -->
  <g transform="translate(505, 190)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="8" y="8" width="40" height="40" rx="4" />
    <rect x="18" y="18" width="20" height="20" stroke-width="3" />
    <line x1="18" y1="2" x2="18" y2="8" />
    <line x1="28" y1="2" x2="28" y2="8" />
    <line x1="38" y1="2" x2="38" y2="8" />
    <line x1="18" y1="48" x2="18" y2="54" />
    <line x1="28" y1="48" x2="28" y2="54" />
    <line x1="38" y1="48" x2="38" y2="54" />
  </g>
  <text x="575" y="228" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">netfilter</text>

  <!-- conntrack card inside netfilter (x = 450, y = 260, w = 300, h = 430) -->
  <rect id="box-conntrack" x="450" y="260" width="300" height="430" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  <text x="600" y="306" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#207448">conntrack</text>

  <!-- Note: two side-by-side insertion slots -->
  <text x="600" y="352" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="600" dy="0">two side-by-side</tspan>
    <tspan x="600" dy="32">insertion slots</tspan>
  </text>

  <!-- Two visual slots side-by-side inside conntrack -->
  <!-- Slot 1 (for A query) -->
  <rect id="slot-1" x="465" y="405" width="125" height="260" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  <!-- Slot 2 (for AAAA query) -->
  <rect id="slot-2" x="610" y="405" width="125" height="260" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />

  <!-- ======================================================== -->
  <!-- STEP 2: kube-proxy DNAT (x = 810, y = 180, w = 360, h = 530) -->
  <!-- ======================================================== -->
  <rect id="box-dnat-outer" x="810" y="180" width="360" height="530" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Step Circle 2 -->
  <circle cx="845" cy="218" r="24" fill="#207448" />
  <text x="845" y="226" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">2</text>

  <!-- Gear / Service Icon -->
  <g transform="translate(885, 190)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="28" cy="28" r="12" />
    <path d="M 28 8 L 28 14 M 28 42 L 28 48 M 8 28 L 14 28 M 42 28 L 48 28 M 14 14 L 18 18 M 38 38 L 42 42 M 14 42 L 18 38 M 38 18 L 42 14" />
  </g>

  <!-- Card labelled kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC (x = 830, y = 260, w = 320, h = 430) -->
  <rect id="box-dnat-card" x="830" y="260" width="320" height="430" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
  
  <text x="990" y="302" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="990" dy="0">kube-proxy DNAT to a</tspan>
    <tspan x="990" dy="32">CoreDNS pod chosen</tspan>
    <tspan x="990" dy="32">by KUBE-SVC</tspan>
  </text>

  <!-- Note: the two packets may go to different CoreDNS pods -->
  <rect id="box-dnat-note" x="845" y="445" width="290" height="220" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  <text x="990" y="520" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="990" dy="0">the two packets may</tspan>
    <tspan x="990" dy="34">go to different</tspan>
    <tspan x="990" dy="34">CoreDNS pods</tspan>
  </text>

  <!-- ======================================================== -->
  <!-- STEP 3: COLLISION & SILENT DROP (x = 1210, y = 180, w = 340, h = 530) -->
  <!-- ======================================================== -->
  <rect id="box-collision-outer" x="1210" y="180" width="340" height="530" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Step Circle 3 -->
  <circle cx="1245" cy="218" r="24" fill="#207448" />
  <text x="1245" y="226" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">3</text>

  <!-- Shield / Security Icon -->
  <g transform="translate(1285, 190)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <path d="M 12 12 L 28 6 L 44 12 C 44 32 28 48 28 48 C 28 48 12 32 12 12 Z" />
  </g>

  <!-- Step 3 Card (x = 1230, y = 260, w = 300, h = 430) -->
  <rect id="box-collision-card" x="1230" y="260" width="300" height="430" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />

  <!-- Label: the second insertion collides with the first -->
  <text x="1380" y="302" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="1380" dy="0">the second insertion</tspan>
    <tspan x="1380" dy="32">collides with the first</tspan>
  </text>

  <!-- Drop box for second insertion -->
  <rect id="box-drop" x="1245" y="445" width="270" height="220" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />

  <!-- Label: insert_failed -->
  <text x="1380" y="550" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">insert_failed</text>

  <!-- Label: the packet is silently dropped -->
  <text x="1380" y="600" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1380" dy="0">the packet is</tspan>
    <tspan x="1380" dy="32">silently dropped</tspan>
  </text>

  <!-- ======================================================== -->
  <!-- ARROWS AND FLOW THROUGH STAGES                           -->
  <!-- ======================================================== -->

  <!-- Upper Flow: A query -->
  <!-- Line from UDP socket (x=356, y=340) to Netfilter slot 1 (x=465, y=435) -->
  <path d="M 356 340 L 395 340 Q 410 340 410 435 L 463 435" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <!-- Label: A query -->
  <text x="408" y="330" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">A query</text>

  <!-- From Netfilter slot 1 through DNAT to Step 3 -->
  <line x1="590" y1="435" x2="828" y2="435" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <line x1="1150" y1="435" x2="1228" y2="435" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <line x1="1230" y1="435" x2="1490" y2="435" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- Lower Flow: AAAA query -->
  <!-- Line from UDP socket (x=356, y=370) to Netfilter slot 2 (x=610, y=575) -->
  <path d="M 356 370 L 385 370 Q 405 370 405 475 L 405 545 Q 405 575 435 575 L 608 575" fill="none" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <!-- Label: AAAA query -->
  <text x="408" y="500" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">AAAA query</text>

  <!-- From Netfilter slot 2 through DNAT to Step 3 collision -->
  <line x1="735" y1="575" x2="828" y2="575" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <line x1="1150" y1="575" x2="1275" y2="575" stroke="#207448" stroke-width="3.5" />

  <!-- COLLISION X (RED-ORANGE ONLY ON THIS ELEMENT) -->
  <g stroke="#db8129" stroke-width="6" stroke-linecap="round">
    <line x1="1265" y1="490" x2="1295" y2="520" />
    <line x1="1295" y1="490" x2="1265" y2="520" />
  </g>

  <!-- ======================================================== -->
  <!-- ROW 2: GREEN FIX PATH (y = 750 to y = 910, h = 160)      -->
  <!-- ======================================================== -->

  <!-- Box 1: NodeLocal DNSCache removes the DNAT with a NOTRACK note -->
  <rect id="box-fix-1" x="50" y="750" width="470" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <!-- Outline Icon: Shield / Cache -->
  <g transform="translate(75, 802)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="48" height="44" rx="4" />
    <line x1="4" y1="20" x2="52" y2="20" />
    <line x1="18" y1="32" x2="38" y2="32" />
  </g>
  <text x="300" y="802" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="300" dy="0" font-weight="bold" fill="#207448">NodeLocal DNSCache removes</tspan>
    <tspan x="300" dy="34">the DNAT with a NOTRACK note</tspan>
  </text>

  <!-- Box 2: single-request-reopen separates the two queries -->
  <rect id="box-fix-2" x="565" y="750" width="470" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <!-- Outline Icon: Split Paths -->
  <g transform="translate(590, 802)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="12" cy="28" r="6" />
    <path d="M 18 28 L 32 16 L 46 16 M 32 16 L 40 10 M 32 40 L 46 40 M 18 28 L 32 40" />
  </g>
  <text x="815" y="802" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="815" dy="0" font-family="monospace" font-weight="bold" fill="#207448">single-request-reopen</tspan>
    <tspan x="815" dy="34">separates the two queries</tspan>
  </text>

  <!-- Box 3: TCP to DNS avoids the UDP path -->
  <rect id="box-fix-3" x="1080" y="750" width="470" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
  <!-- Outline Icon: TCP Handshake / Connection -->
  <g transform="translate(1105, 802)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="6" y="10" width="20" height="36" rx="3" />
    <rect x="30" y="10" width="20" height="36" rx="3" />
    <line x1="12" y1="28" x2="44" y2="28" />
  </g>
  <text x="1330" y="802" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
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
    f.write(build_svg())

print("Built test_candidate_dns.svg (v3)")
