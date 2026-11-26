import re
import xml.etree.ElementTree as ET

def generate_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>A full conntrack table: new connections fail, old ones keep working</title>
  <desc>A full conntrack table: new connections fail, old ones keep working</desc>

  <defs>
    <!-- Arrowhead green -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <!-- Arrowhead orange -->
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Title (48px bold) -->
  <text x="800" y="56" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">A full conntrack table: </tspan>
    <tspan x="800" dy="54">new connections fail, old ones keep working</tspan>
  </text>

  <!-- ==================== UPPER SECTION: FLOWS & TABLE ==================== -->

  <!-- Left Container: Existing Flows (Green) -->
  <g id="box-existing-flows">
    <rect x="40" y="136" width="340" height="384" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Stream / Active packet icon (56px, stroke 4, #207448) -->
    <g transform="translate(182, 154)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 12 C 18 6, 38 6, 50 12" />
      <path d="M 6 28 C 18 22, 38 22, 50 28" />
      <path d="M 6 44 C 18 38, 38 38, 50 44" />
      <circle cx="28" cy="28" r="6" fill="#207448" />
    </g>
    <!-- Card inside Left Container -->
    <rect x="60" y="240" width="300" height="180" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="210" y="295" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="210" dy="0">established flow: </tspan>
      <tspan x="210" dy="38">keeps its slot, </tspan>
      <tspan x="210" dy="38">works</tspan>
    </text>
  </g>

  <!-- Three green arrows from existing flows to center table -->
  <line x1="380" y1="300" x2="440" y2="300" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />
  <line x1="380" y1="365" x2="440" y2="365" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />
  <line x1="380" y1="430" x2="440" y2="430" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- Center Container: Conntrack Table Box -->
  <g id="box-conntrack-table">
    <rect x="440" y="136" width="720" height="384" rx="16" fill="#ffffff" stroke="#207448" stroke-width="3" />

    <!-- Table Icon (56px, stroke 4, #207448) -->
    <g transform="translate(468, 150)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="48" height="44" rx="6" />
      <line x1="4" y1="20" x2="52" y2="20" />
      <line x1="4" y1="34" x2="52" y2="34" />
      <line x1="20" y1="6" x2="20" y2="50" />
    </g>

    <!-- Center Box Title (30px bold) -->
    <text x="825" y="185" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">conntrack table (hash table)</text>

    <!-- Subtitle / State Badge: nf_conntrack_count = nf_conntrack_max -->
    <rect x="490" y="214" width="620" height="58" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="800" y="251" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">nf_conntrack_count = nf_conntrack_max</text>

    <!-- Slot Row 1 (Visual full slot representation) -->
    <g transform="translate(460, 286)">
      <rect x="0" y="0" width="680" height="42" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <rect x="12" y="8" width="130" height="26" rx="4" fill="#207448" opacity="0.35" />
      <rect x="155" y="8" width="80" height="26" rx="4" fill="#207448" opacity="0.25" />
      <rect x="250" y="8" width="160" height="26" rx="4" fill="#207448" opacity="0.35" />
      <rect x="425" y="8" width="80" height="26" rx="4" fill="#207448" opacity="0.25" />
      <rect x="520" y="8" width="145" height="26" rx="4" fill="#207448" opacity="0.5" />
    </g>

    <!-- Slot Row 2: Tuple Label Card -->
    <g transform="translate(460, 342)">
      <rect x="0" y="0" width="680" height="114" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
      <text x="340" y="38" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
        <tspan x="340" dy="0">source address, source port, </tspan>
        <tspan x="340" dy="34">destination address, destination port, </tspan>
        <tspan x="340" dy="34">protocol</tspan>
      </text>
    </g>

    <!-- Slot Row 3 (Visual full slot representation) -->
    <g transform="translate(460, 468)">
      <rect x="0" y="0" width="680" height="40" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <rect x="12" y="7" width="140" height="26" rx="4" fill="#207448" opacity="0.35" />
      <rect x="165" y="7" width="75" height="26" rx="4" fill="#207448" opacity="0.25" />
      <rect x="255" y="7" width="150" height="26" rx="4" fill="#207448" opacity="0.35" />
      <rect x="420" y="7" width="85" height="26" rx="4" fill="#207448" opacity="0.25" />
      <rect x="520" y="7" width="145" height="26" rx="4" fill="#207448" opacity="0.5" />
    </g>
  </g>

  <!-- Right: Closed door barrier & arrows -->
  <!-- Closed Door Barrier at x = 1160 -->
  <g id="closed-door" transform="translate(1148, 275)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="0" y="0" width="24" height="180" rx="4" fill="#fff9f3" stroke="#db8129" stroke-width="3" />
    <line x1="4" y1="40" x2="20" y2="40" />
    <line x1="4" y1="90" x2="20" y2="90" />
    <line x1="4" y1="140" x2="20" y2="140" />
    <circle cx="8" cy="90" r="3" fill="#db8129" />
  </g>

  <!-- Three orange arrows from new flows hitting the closed door -->
  <line x1="1220" y1="300" x2="1176" y2="300" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />
  <line x1="1220" y1="365" x2="1176" y2="365" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />
  <line x1="1220" y1="430" x2="1176" y2="430" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />

  <!-- Right Container: New Connections (Orange Highlight) -->
  <g id="box-new-connections">
    <rect x="1220" y="136" width="340" height="384" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />
    <!-- Lock / Closed Gate Icon (56px, stroke 4, #db8129) -->
    <g transform="translate(1362, 154)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="20" width="40" height="30" rx="4" />
      <path d="M 16 20 V 12 C 16 6, 40 6, 40 12 V 20" />
      <circle cx="28" cy="35" r="3" fill="#db8129" />
    </g>
    <!-- Card inside Right Container -->
    <rect x="1240" y="240" width="300" height="180" rx="12" fill="#fff9f3" stroke="#db8129" stroke-width="2" />
    <text x="1390" y="295" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="1390" dy="0">new connection: </tspan>
      <tspan x="1390" dy="38">no space, </tspan>
      <tspan x="1390" dy="38">cannot be made</tspan>
    </text>
  </g>

  <!-- ==================== NUMBERED STRIP BELOW TABLE ==================== -->
  <rect x="40" y="546" width="1520" height="248" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />

  <!-- Step 1 Card -->
  <g id="strip-step-1">
    <rect x="60" y="566" width="460" height="208" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <!-- Circle 1 -->
    <circle cx="100" cy="606" r="24" fill="#207448" />
    <text x="100" y="615" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
      <tspan x="100" dy="0">1 </tspan>
      <tspan x="80" dy="48" text-anchor="start" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">Read the two numbers: </tspan>
      <tspan x="80" dy="36" text-anchor="start" font-family="monospace" font-size="24" fill="#303a36">sysctl </tspan>
      <tspan x="80" dy="34" text-anchor="start" font-family="monospace" font-size="24" fill="#207448">net.netfilter.nf_conntrack_count </tspan>
      <tspan x="80" dy="34" text-anchor="start" font-family="monospace" font-size="24" fill="#207448">and nf_conntrack_max</tspan>
    </text>
  </g>

  <!-- Step 2 Card -->
  <g id="strip-step-2">
    <rect x="540" y="566" width="450" height="96" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <!-- Circle 2 -->
    <circle cx="580" cy="614" r="24" fill="#207448" />
    <text x="580" y="623" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
      <tspan x="580" dy="0">2 </tspan>
      <tspan x="625" dy="0" text-anchor="start" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">Divide: count / max</tspan>
    </text>
  </g>

  <!-- Established Timeout Card -->
  <g id="strip-timeout">
    <rect x="540" y="678" width="450" height="96" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <!-- Clock Icon (stroke 3.5, #207448) -->
    <g transform="translate(558, 698)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="24" cy="24" r="20" />
      <polyline points="24,12 24,24 32,28" />
    </g>
    <text x="620" y="722" text-anchor="start" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="620" dy="0">Established timeout default: </tspan>
      <tspan x="620" dy="34">432000 seconds, five days</tspan>
    </text>
  </g>

  <!-- Step 3 Card -->
  <g id="strip-step-3">
    <rect x="1010" y="566" width="530" height="208" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <!-- Circle 3 -->
    <circle cx="1050" cy="606" r="24" fill="#207448" />
    <text x="1050" y="615" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
      <tspan x="1050" dy="0">3 </tspan>
      <tspan x="1095" dy="0" text-anchor="start" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">Watch the trend: </tspan>
      <tspan x="1030" dy="36" text-anchor="start" font-family="sans-serif" font-size="24" fill="#303a36">read twice; climbing and staying = </tspan>
      <tspan x="1030" dy="34" text-anchor="start" font-family="sans-serif" font-size="24" fill="#207448">flows arrive faster than they leave; </tspan>
      <tspan x="1030" dy="34" text-anchor="start" font-family="sans-serif" font-size="24" fill="#303a36">rising then falling = a burst</tspan>
    </text>
  </g>

  <!-- ==================== SIDE NOTE & FIX LIST ==================== -->

  <!-- Side Note Box (Kube-proxy...) -->
  <g id="box-side-note">
    <rect x="40" y="818" width="840" height="276" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Gear / Service Outline Icon (56px, stroke 4, #207448) -->
    <g transform="translate(68, 836)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="12" />
      <path d="M 28 6 L 28 16 M 28 40 L 28 50 M 6 28 L 16 28 M 40 28 L 50 28 M 12 12 L 20 20 M 36 36 L 44 44 M 12 44 L 20 36 M 36 20 L 44 12" />
    </g>
    <!-- Text Card -->
    <rect x="64" y="904" width="792" height="170" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="84" y="942" text-anchor="start" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="84" dy="0" font-weight="bold">Kube-proxy Service load balancing through iptables </tspan>
      <tspan x="84" dy="36">depends on conntrack, so a full table looks like </tspan>
      <tspan x="84" dy="36">Service flakiness; pods on one node share that </tspan>
      <tspan x="84" dy="36">node's table.</tspan>
    </text>
  </g>

  <!-- Fix List Box -->
  <g id="box-fix-list">
    <rect x="900" y="818" width="660" height="276" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    <!-- Tool / Wrench Outline Icon (56px, stroke 4, #207448) -->
    <g transform="translate(928, 836)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 40 10 C 35 5, 25 5, 20 10 L 10 20 C 5 25, 5 35, 10 40 L 18 48 C 22 52, 28 52, 32 48 L 48 32 C 52 28, 52 22, 48 18 Z" />
      <circle cx="22" cy="22" r="4" fill="#207448" />
    </g>
    <!-- Text Card -->
    <rect x="924" y="904" width="612" height="170" rx="12" fill="#ffffff" stroke="#207448" stroke-width="1.5" />
    <text x="944" y="955" text-anchor="start" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">
      <tspan x="944" dy="0">raise the maximum if memory allows, </tspan>
      <tspan x="944" dy="40">reuse connections, find the client </tspan>
      <tspan x="944" dy="40">opening connections in a loop</tspan>
    </text>
  </g>

  <!-- ==================== TAKEAWAY BAR ==================== -->
  <rect x="40" y="1120" width="1520" height="56" rx="10" fill="#207448" />
  <text x="800" y="1156" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">For any new connections fail, old ones work symptom, compare conntrack count to max first.</text>
</svg>'''
    return svg

if __name__ == "__main__":
    from test_harness import test_svg
    svg = generate_svg()
    with open("conntrack.svg", "w") as f:
        f.write(svg)
    test_svg(svg)
