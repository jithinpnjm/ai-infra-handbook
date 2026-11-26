import xml.etree.ElementTree as ET
import re

def build_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>How parallel A and AAAA queries race in conntrack and cause a 5-second stall</title>
  <desc>Infographic illustrating how parallel A and AAAA DNS queries from a single UDP socket race during conntrack DNAT entry confirmation in Kubernetes, resulting in insert_failed, silent packet drops, and 5-second glibc resolver timeouts, along with three fix strategies.</desc>

  <defs>
    <!-- Arrowhead Green (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5" />

  <!-- ==================== TITLE (48px bold) ==================== -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">How parallel A and AAAA queries race</tspan>
    <tspan x="800" dy="54">in conntrack and cause a 5-second stall</tspan>
  </text>

  <!-- ==================== ROW 1: THE RACE FLOW ==================== -->

  <!-- ===== COLUMN 1: POD CONTAINER ===== -->
  <g id="col-pod">
    <!-- Pod Container Panel -->
    <rect x="40" y="140" width="370" height="520" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Application / Pod Window Icon (56px, stroke 4, green) -->
    <g transform="translate(60, 156)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="8" width="48" height="40" rx="6" />
      <line x1="4" y1="20" x2="52" y2="20" />
      <circle cx="12" cy="14" r="2" fill="#207448" />
      <circle cx="20" cy="14" r="2" fill="#207448" />
      <circle cx="28" cy="14" r="2" fill="#207448" />
    </g>

    <!-- Node Title: pod -->
    <text x="130" y="195" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">pod</text>

    <!-- Glibc Resolver Box -->
    <rect x="58" y="222" width="334" height="236" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="225" y="256" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">glibc resolver</text>

    <!-- One UDP Socket Card -->
    <rect x="74" y="274" width="302" height="66" rx="8" fill="#f8faf8" stroke="#207448" stroke-width="1.5" />
    <text x="225" y="315" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">one UDP socket</text>

    <!-- Note: both to the same source IP and port -->
    <rect x="74" y="352" width="302" height="92" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1" />
    <text x="225" y="388" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="225" dy="0">both to the same</tspan>
      <tspan x="225" dy="32">source IP and port</tspan>
    </text>

    <!-- Step 4 Box on Pod side: Clock icon + waits for default 5 s timeout, then retries -->
    <rect x="58" y="476" width="334" height="166" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    
    <!-- Step 4 Circle -->
    <circle cx="86" cy="506" r="24" fill="#207448" />
    <text x="86" y="506" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>

    <!-- Clock Icon (56px outline, green stroke 4) -->
    <g transform="translate(120, 480)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <polyline points="28,14 28,28 40,28" />
    </g>

    <!-- Label: waits for default 5 s timeout, then retries -->
    <text x="225" y="566" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="225" dy="0">waits for default 5 s</tspan>
      <tspan x="225" dy="32">timeout, then retries</tspan>
    </text>
  </g>

  <!-- ===== QUERY ARROWS (LEAVING UDP SOCKET TOWARDS STEP 1) ===== -->
  <!-- Top Arrow: A query -->
  <line x1="392" y1="292" x2="492" y2="292" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="442" y="276" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">A query</text>

  <!-- Bottom Arrow: AAAA query -->
  <line x1="392" y1="324" x2="492" y2="324" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <text x="442" y="358" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">AAAA query</text>

  <!-- ===== COLUMN 2: STEP 1 NETFILTER / CONNTRACK ===== -->
  <g id="col-netfilter">
    <!-- Step 1 Circle above box -->
    <circle cx="510" cy="164" r="24" fill="#207448" />
    <text x="510" y="164" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>

    <!-- Netfilter Container Box -->
    <rect x="494" y="140" width="346" height="520" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Shield / Netfilter Security Icon (56px, stroke 4, green) -->
    <g transform="translate(546, 156)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 V 30 C 48 44 28 52 28 52 C 28 52 8 44 8 30 V 14 Z" />
      <line x1="28" y1="18" x2="28" y2="38" />
    </g>

    <!-- Node Title: netfilter -->
    <text x="616" y="195" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">netfilter</text>

    <!-- Conntrack Card -->
    <rect x="512" y="222" width="310" height="420" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="667" y="258" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">conntrack</text>

    <!-- Label: two side-by-side insertion slots -->
    <rect x="524" y="274" width="286" height="74" rx="8" fill="#f8faf8" stroke="#207448" stroke-width="1.5" />
    <text x="667" y="306" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="667" dy="0">two side-by-side</tspan>
      <tspan x="667" dy="30">insertion slots</tspan>
    </text>

    <!-- Visual Insertion Slot 1 (for A query) -->
    <rect x="532" y="364" width="130" height="110" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4" />
    <!-- Visual Insertion Slot 2 (for AAAA query) -->
    <rect x="674" y="364" width="130" height="110" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="6 4" />

    <!-- Internal path lines showing slots -->
    <line x1="597" y1="364" x2="597" y2="474" stroke="#207448" stroke-width="2" />
    <line x1="739" y1="364" x2="739" y2="474" stroke="#207448" stroke-width="2" />

    <!-- Unconfirmed status hint visually -->
    <rect x="524" y="494" width="286" height="130" rx="8" fill="#f8faf8" stroke="#207448" stroke-width="1" />
    <!-- Arrow pass-through tracks -->
    <line x1="500" y1="540" x2="820" y2="540" stroke="#207448" stroke-width="3" stroke-dasharray="4 4" />
    <line x1="500" y1="580" x2="820" y2="580" stroke="#207448" stroke-width="3" stroke-dasharray="4 4" />
  </g>

  <!-- ===== ARROWS TO STEP 2 ===== -->
  <line x1="840" y1="292" x2="904" y2="292" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <line x1="840" y1="324" x2="904" y2="324" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ===== COLUMN 3: STEP 2 KUBE-PROXY DNAT ===== -->
  <g id="col-kubeproxy">
    <!-- Step 2 Circle above box -->
    <circle cx="920" cy="164" r="24" fill="#207448" />
    <text x="920" y="164" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>

    <!-- kube-proxy Container Box -->
    <rect x="904" y="140" width="336" height="520" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Gear / Service Network Icon (56px, stroke 4, green) -->
    <g transform="translate(956, 156)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="14" />
      <path d="M 28 4 V 12 M 28 44 V 52 M 4 28 H 12 M 44 28 H 52 M 11 11 L 17 17 M 39 39 L 45 45 M 11 45 L 17 39 M 39 17 L 45 11" />
    </g>

    <!-- Box Label: kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC -->
    <rect x="918" y="222" width="308" height="236" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1072" y="260" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1072" dy="0">kube-proxy DNAT to a</tspan>
      <tspan x="1072" dy="32">CoreDNS pod chosen</tspan>
      <tspan x="1072" dy="32">by </tspan><tspan font-family="monospace">KUBE-SVC</tspan>
    </text>

    <!-- Note inside Step 2: the two packets may go to different CoreDNS pods -->
    <rect x="926" y="374" width="292" height="72" rx="8" fill="#f8faf8" stroke="#207448" stroke-width="1.5" />
    <!-- Visual bifurcation / spread icon -->
    <line x1="936" y1="480" x2="1208" y2="480" stroke="#207448" stroke-width="2" stroke-dasharray="6 4" />

    <rect x="918" y="476" width="308" height="166" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1072" y="530" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1072" dy="0">the two packets may go to</tspan>
      <tspan x="1072" dy="32">different CoreDNS pods</tspan>
    </text>
  </g>

  <!-- ===== ARROWS TO STEP 3 ===== -->
  <!-- Top packet (A query): succeeds through to CoreDNS pod -->
  <line x1="1240" y1="292" x2="1310" y2="292" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />
  <!-- Bottom packet (AAAA query): races for insertion -->
  <line x1="1240" y1="410" x2="1310" y2="410" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />

  <!-- ===== COLUMN 4: STEP 3 INSERTION COLLISION & DROP ===== -->
  <g id="col-collision">
    <!-- Step 3 Circle above box -->
    <circle cx="1326" cy="164" r="24" fill="#207448" />
    <text x="1326" y="164" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>

    <!-- Step 3 Container Box -->
    <rect x="1310" y="140" width="250" height="520" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

    <!-- Cross / Collision Warning Icon (56px, stroke 4, green) -->
    <g transform="translate(1362, 156)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22" />
      <line x1="28" y1="16" x2="28" y2="30" />
      <circle cx="28" cy="38" r="2" fill="#207448" />
    </g>

    <!-- Top Card: First insertion succeeds (A query proceeds) -->
    <rect x="1324" y="240" width="222" height="96" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <polyline points="1350,288 1365,302 1395,270" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round" />
    <circle cx="1470" cy="288" r="16" fill="#e8f1ea" stroke="#207448" stroke-width="2" />

    <!-- Label: the second insertion collides with the first -->
    <rect x="1324" y="352" width="222" height="124" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <text x="1435" y="390" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1435" dy="0">the second insertion</tspan>
      <tspan x="1435" dy="30">collides with</tspan>
      <tspan x="1435" dy="30">the first</tspan>
    </text>

    <!-- THE RED-ORANGE COLLISION X (THE ONLY ORANGE ELEMENT) -->
    <g id="collision-x" transform="translate(1395, 492)">
      <!-- Orange X lines with #db8129 -->
      <line x1="10" y1="10" x2="70" y2="70" stroke="#db8129" stroke-width="8" stroke-linecap="round" />
      <line x1="70" y1="10" x2="10" y2="70" stroke="#db8129" stroke-width="8" stroke-linecap="round" />
    </g>

    <!-- Label: insert_failed -->
    <text x="1435" y="596" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">insert_failed</text>

    <!-- Label: the packet is silently dropped -->
    <text x="1435" y="632" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1435" dy="0">the packet is</tspan>
      <tspan x="1435" dy="28">silently dropped</tspan>
    </text>
  </g>

  <!-- Dotted return path from dropped packet back to Step 4 on pod side -->
  <path d="M 1310 610 H 420 V 559 H 392" fill="none" stroke="#207448" stroke-width="2.5" stroke-dasharray="8 6" marker-end="url(#arrow-green)" />

  <!-- ==================== ROW 2: FIX PATH (THREE SMALL BOXES) ==================== -->
  <g id="row-fix-path">
    <!-- Box 1: NodeLocal DNSCache removes the DNAT with a NOTRACK note -->
    <rect x="40" y="690" width="480" height="230" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Memory / Cache Shield Icon (56px) -->
    <g transform="translate(68, 712)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="10" width="44" height="38" rx="6" />
      <line x1="6" y1="22" x2="50" y2="22" />
      <line x1="18" y1="34" x2="38" y2="34" />
      <circle cx="14" cy="16" r="2" fill="#207448" />
    </g>
    <text x="280" y="784" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="280" dy="0">NodeLocal DNSCache</tspan>
      <tspan x="280" dy="34">removes the DNAT with</tspan>
      <tspan x="280" dy="34">a </tspan><tspan font-family="monospace">NOTRACK</tspan><tspan> note</tspan>
    </text>

    <!-- Box 2: single-request-reopen separates the two queries -->
    <rect x="560" y="690" width="480" height="230" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Sequence / Reopen Fork Icon (56px) -->
    <g transform="translate(588, 712)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="14" cy="28" r="8" />
      <circle cx="42" cy="16" r="8" />
      <circle cx="42" cy="40" r="8" />
      <path d="M 22 28 H 34 M 34 16 V 40" />
    </g>
    <text x="800" y="796" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="800" dy="0" font-family="monospace">single-request-reopen</tspan>
      <tspan x="800" dy="36">separates the two queries</tspan>
    </text>

    <!-- Box 3: TCP to DNS avoids the UDP path -->
    <rect x="1080" y="690" width="480" height="230" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- TCP Stream / Cable Icon (56px) -->
    <g transform="translate(1108, 712)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="14" width="40" height="28" rx="6" />
      <line x1="18" y1="42" x2="18" y2="52" />
      <line x1="38" y1="42" x2="38" y2="52" />
      <line x1="20" y1="24" x2="36" y2="24" />
      <line x1="20" y1="32" x2="30" y2="32" />
    </g>
    <text x="1320" y="796" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1320" dy="0">TCP to DNS avoids</tspan>
      <tspan x="1320" dy="36">the UDP path</tspan>
    </text>
  </g>

  <!-- ==================== TAKEAWAY BAR AT BOTTOM ==================== -->
  <rect x="40" y="960" width="1520" height="80" rx="12" fill="#207448" />
  <text x="800" y="1008" text-anchor="middle" dominant-baseline="central" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">two parallel queries on one socket can collide in the kernel, and the lost packet costs a timeout.</text>
</svg>'''
    return svg

if __name__ == "__main__":
    with open("candidate_conntrack_race.svg", "w") as f:
        f.write(build_svg())
    print("Saved candidate_conntrack_race.svg")
