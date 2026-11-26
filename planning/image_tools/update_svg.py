import os

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Three paths from a container: to a neighbour, to the Internet, and from outside to a published port</title>
  <desc>Technical infographic illustrating the three container networking paths: c1 to c2 over a bridge, c1 to the Internet with NAT masquerading, and inbound traffic to a published port with DNAT.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129"/>
    </marker>
    <filter id="shadow" x="-2%" y="-4%" width="104%" height="108%">
      <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.05"/>
    </filter>
  </defs>

  <!-- Canvas Background -->
  <rect width="1600" height="1200" fill="#f5f8f5"/>

  <!-- ==================== TITLE (at most 2 lines, 48px bold) ==================== -->
  <text x="800" y="80" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">Three paths from a container: to a neighbour,</text>
  <text x="800" y="132" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="#303a36">to the Internet, and to a published port</text>

  <!-- ==================== SHARED HOST CONTAINER ==================== -->
  <rect id="box-host" x="40" y="154" width="1520" height="780" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" stroke-dasharray="10 8" filter="url(#shadow)"/>

  <!-- Host Header Bar & Shared Nodes -->
  <rect id="box-host-header" x="56" y="166" width="1488" height="86" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>

  <!-- Host Badge & Server Icon -->
  <g transform="translate(70, 181)">
    <!-- 56px Host Icon (outline, stroke 4, green) -->
    <g stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="6" width="52" height="18" rx="3"/>
      <rect x="2" y="30" width="52" height="18" rx="3"/>
      <circle cx="12" cy="15" r="2" fill="#207448"/>
      <circle cx="20" cy="15" r="2" fill="#207448"/>
      <circle cx="12" cy="39" r="2" fill="#207448"/>
      <circle cx="20" cy="39" r="2" fill="#207448"/>
      <line x1="36" y1="15" x2="48" y2="15"/>
      <line x1="36" y1="39" x2="48" y2="39"/>
    </g>
    <!-- Host Label -->
    <rect x="66" y="6" width="82" height="44" rx="6" fill="#207448"/>
    <text x="107" y="37" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">host</text>
  </g>

  <!-- Shared Node 1: c1 (10.10.0.11) -->
  <g transform="translate(246, 175)">
    <rect x="0" y="0" width="290" height="68" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Container Icon (56px, stroke 4) -->
    <g transform="translate(10, 6)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="46" height="48" rx="4"/>
      <line x1="2" y1="16" x2="48" y2="16"/>
      <circle cx="10" cy="9" r="2.5" fill="#207448"/>
      <circle cx="19" cy="9" r="2.5" fill="#207448"/>
    </g>
    <text x="74" y="43" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">c1 (10.10.0.11)</text>
  </g>

  <!-- Shared Node 2: br0 (10.10.0.1/24) -->
  <g transform="translate(552, 175)">
    <rect x="0" y="0" width="314" height="68" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Bridge Icon (56px, stroke 4) -->
    <g transform="translate(10, 6)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="8" width="46" height="34" rx="4"/>
      <line x1="14" y1="20" x2="14" y2="30"/>
      <line x1="25" y1="20" x2="25" y2="30"/>
      <line x1="36" y1="20" x2="36" y2="30"/>
    </g>
    <text x="74" y="43" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">br0 (10.10.0.1/24)</text>
  </g>

  <!-- Shared Node 3: c2 (10.10.0.12) -->
  <g transform="translate(882, 175)">
    <rect x="0" y="0" width="290" height="68" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Container Icon (56px, stroke 4) -->
    <g transform="translate(10, 6)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="2" width="46" height="48" rx="4"/>
      <line x1="2" y1="16" x2="48" y2="16"/>
      <circle cx="10" cy="9" r="2.5" fill="#207448"/>
      <circle cx="19" cy="9" r="2.5" fill="#207448"/>
    </g>
    <text x="74" y="43" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">c2 (10.10.0.12)</text>
  </g>

  <!-- Shared Node 4: uplink NIC -->
  <g transform="translate(1188, 175)">
    <rect x="0" y="0" width="340" height="68" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- NIC Icon (56px, stroke 4) -->
    <g transform="translate(12, 6)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="46" height="38" rx="3"/>
      <line x1="10" y1="42" x2="10" y2="50"/>
      <line x1="20" y1="42" x2="20" y2="50"/>
      <line x1="30" y1="42" x2="30" y2="50"/>
      <line x1="40" y1="42" x2="40" y2="50"/>
      <circle cx="14" cy="18" r="3" fill="#207448"/>
    </g>
    <text x="76" y="43" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">uplink NIC</text>
  </g>

  <!-- ==================== LANE 1 ==================== -->
  <g id="lane-1">
    <rect id="box-lane-1" x="56" y="264" width="1488" height="218" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    
    <!-- Number Circle 1 -->
    <circle cx="96" cy="300" r="24" fill="#207448"/>
    <text x="96" y="309" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>
    
    <!-- Lane 1 Icon (L2 Bridge Switch outline, 56px, stroke 4) -->
    <g transform="translate(136, 272)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="14" cy="28" r="8"/>
      <circle cx="42" cy="28" r="8"/>
      <path d="M 22 28 L 34 28"/>
    </g>
    
    <!-- Title -->
    <text x="208" y="310" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">c1 to c2 on the same bridge</text>

    <!-- Path Arrow across Lane 1 -->
    <line x1="680" y1="300" x2="1520" y2="300" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Lane 1 Content Lines -->
    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="84" y="348">c1's own stack routes the packet because both share a subnet, ARP finds c2,</tspan>
      <tspan x="84" y="376">the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns</tspan>
      <tspan x="84" y="404">the MAC and forwards the frame to c2's veth and eth0</tspan>
      <tspan x="84" y="432">br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic;</tspan>
      <tspan x="84" y="460">Kubernetes requires it so kube-proxy rules apply</tspan>
    </text>
  </g>

  <!-- ==================== LANE 2 ==================== -->
  <g id="lane-2">
    <rect id="box-lane-2" x="56" y="494" width="1488" height="276" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5"/>
    
    <!-- Number Circle 2 -->
    <circle cx="96" cy="528" r="24" fill="#207448"/>
    <text x="96" y="537" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>

    <!-- Lane 2 Icon (Globe / Internet outline, 56px, stroke 4) -->
    <g transform="translate(136, 500)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <ellipse cx="28" cy="28" rx="10" ry="22"/>
      <line x1="6" y1="28" x2="50" y2="28"/>
    </g>

    <!-- Title -->
    <text x="208" y="538" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#207448">c1 to the Internet</text>

    <!-- Path Arrow across Lane 2 -->
    <line x1="530" y1="528" x2="1520" y2="528" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

    <!-- Explanation Text -->
    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="84" y="578">default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack,</tspan>
      <tspan x="84" y="604">passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's</tspan>
      <tspan x="84" y="630">address; return traffic is un-NATed by conntrack and delivered back through the bridge;</tspan>
      <tspan x="84" y="656">the outside world only talks to the host</tspan>
    </text>

    <!-- Commands (monospace) -->
    <text font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="84" y="688">sysctl -w net.ipv4.ip_forward=1</tspan>
      <tspan x="620" y="688">iptables -I FORWARD -i br0 -j ACCEPT</tspan>
      <tspan x="84" y="716">iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE</tspan>
      <tspan x="84" y="744">iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT</tspan>
    </text>
  </g>

  <!-- ==================== LANE 3 (Orange Accent) ==================== -->
  <g id="lane-3">
    <rect id="box-lane-3" x="56" y="782" width="1488" height="138" rx="10" fill="#fdf8f3" stroke="#db8129" stroke-width="2.5"/>
    
    <!-- Number Circle 3 (Orange) -->
    <circle cx="96" cy="818" r="24" fill="#db8129"/>
    <text x="96" y="827" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>

    <!-- Lane 3 Icon (DNAT port redirect outline, 56px, stroke 4, orange) -->
    <g transform="translate(136, 790)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="4"/>
      <path d="M 18 28 L 38 28"/>
      <polyline points="26,20 18,28 26,36"/>
    </g>

    <!-- Title (Orange) -->
    <text x="208" y="828" font-family="system-ui, -apple-system, sans-serif" font-size="30" font-weight="bold" fill="#db8129">host:8080 to c1:80</text>

    <!-- Inbound Path Arrow (Orange, points right-to-left towards container) -->
    <line x1="1520" y1="818" x2="520" y2="818" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)"/>

    <!-- Lane 3 Commands -->
    <text font-family="ui-monospace, monospace" font-size="24" fill="#303a36">
      <tspan x="84" y="864">iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.10.0.11:80</tspan>
      <tspan x="84" y="894">iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8080 -j DNAT ... for local clients</tspan>
    </text>
  </g>

  <!-- ==================== FOOTER & DOCKER NOTE ==================== -->
  <g id="footer-notes">
    <rect id="box-footer" x="40" y="946" width="1520" height="142" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" filter="url(#shadow)"/>
    
    <!-- DNS Inside Note -->
    <text font-family="ui-monospace, monospace" font-size="24" font-weight="bold" fill="#207448" x="64" y="982">DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf</text>
    
    <!-- Divider Line -->
    <line x1="64" y1="998" x2="1536" y2="998" stroke="#207448" stroke-width="1.5" stroke-opacity="0.3"/>

    <!-- Docker Note -->
    <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
      <tspan x="64" y="1024">almost literally what the default bridge network does: docker0, a veth per container,</tspan>
      <tspan x="64" y="1048">an IPAM address from a private pool, a default route via the bridge, masquerade,</tspan>
      <tspan x="64" y="1072">DNAT for published ports, a bind-mounted /etc/resolv.conf</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="bottom-bar">
    <rect id="box-takeaway" x="40" y="1100" width="1520" height="58" rx="8" fill="#207448" filter="url(#shadow)"/>
    <text x="800" y="1136" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#ffffff">A container is only a namespace plus a cable</text>
  </g>
</svg>"""

with open("test_full_candidate.svg", "w") as f:
    f.write(svg_content)

print("Saved test_full_candidate.svg")
