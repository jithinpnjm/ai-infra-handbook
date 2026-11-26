import re
import xml.etree.ElementTree as ET

svg_code = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>Three paths from a container: to a neighbour, to the Internet, and from outside to a published port</title>
  <desc>Technical architecture diagram illustrating the three fundamental Linux container networking paths: same-bridge container-to-container communication, outbound SNAT masquerade to the Internet, and inbound DNAT port forwarding to published container ports.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerWidth="14" markerHeight="14" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerWidth="14" markerHeight="14" orient="auto-start-reverse">
      <path d="M 2 3 L 16 9 L 2 15 z" fill="#db8129" />
    </marker>
    <style>
      .title { font-family: system-ui, -apple-system, sans-serif; font-size: 48px; font-weight: bold; fill: #303a36; text-anchor: middle; }
      .host-title { font-family: system-ui, -apple-system, sans-serif; font-size: 26px; font-weight: bold; fill: #207448; }
      .section-title { font-family: system-ui, -apple-system, sans-serif; font-size: 30px; font-weight: bold; fill: #207448; }
      .section-title-orange { font-family: system-ui, -apple-system, sans-serif; font-size: 30px; font-weight: bold; fill: #db8129; }
      .node-text { font-family: system-ui, -apple-system, sans-serif; font-size: 24px; font-weight: bold; fill: #303a36; }
      .body-text { font-family: system-ui, -apple-system, sans-serif; font-size: 24px; fill: #303a36; }
      .mono-text { font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, Courier, monospace; font-size: 24px; fill: #303a36; }
      .takeaway-text { font-family: system-ui, -apple-system, sans-serif; font-size: 24px; font-weight: bold; fill: #ffffff; text-anchor: middle; }
      .circle-text { font-family: system-ui, -apple-system, sans-serif; font-size: 26px; font-weight: bold; fill: #ffffff; text-anchor: middle; dominant-baseline: central; }
      .badge-text { font-family: system-ui, -apple-system, sans-serif; font-size: 24px; font-weight: bold; fill: #ffffff; text-anchor: middle; dominant-baseline: central; }
    </style>
  </defs>

  <!-- Background -->
  <rect x="0" y="0" width="1600" height="1200" fill="#f5f8f5" />

  <!-- Canvas Title (at most 2 lines, well inside 1600 canvas) -->
  <text class="title" x="800" y="74">Three paths from a container: to a neighbour,</text>
  <text class="title" x="800" y="118">to the Internet, and outside to a published port</text>

  <!-- Host Container (Subgraph) -->
  <rect x="40" y="164" width="1520" height="728" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="2" stroke-dasharray="8 6" />

  <!-- Host Header & Shared Nodes Panel -->
  <rect x="56" y="180" width="1488" height="56" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />

  <!-- Host Label Badge -->
  <rect x="68" y="188" width="90" height="40" rx="6" fill="#207448" />
  <text class="badge-text" x="113" y="208">host</text>

  <!-- Node 1: c1 (10.10.0.11) -->
  <g transform="translate(180, 188)">
    <rect x="0" y="2" width="36" height="36" rx="4" fill="none" stroke="#207448" stroke-width="3" />
    <line x1="0" y1="12" x2="36" y2="12" stroke="#207448" stroke-width="2" />
    <circle cx="7" cy="7" r="2" fill="#207448" />
    <circle cx="14" cy="7" r="2" fill="#207448" />
    <text class="node-text" x="46" y="27">c1 (10.10.0.11)</text>
  </g>

  <!-- Node 2: br0 (10.10.0.1/24) -->
  <g transform="translate(540, 188)">
    <rect x="0" y="6" width="40" height="28" rx="4" fill="none" stroke="#207448" stroke-width="3" />
    <line x1="10" y1="15" x2="10" y2="25" stroke="#207448" stroke-width="3" />
    <line x1="20" y1="15" x2="20" y2="25" stroke="#207448" stroke-width="3" />
    <line x1="30" y1="15" x2="30" y2="25" stroke="#207448" stroke-width="3" />
    <text class="node-text" x="50" y="27">br0 (10.10.0.1/24)</text>
  </g>

  <!-- Node 3: c2 (10.10.0.12) -->
  <g transform="translate(930, 188)">
    <rect x="0" y="2" width="36" height="36" rx="4" fill="none" stroke="#207448" stroke-width="3" />
    <line x1="0" y1="12" x2="36" y2="12" stroke="#207448" stroke-width="2" />
    <circle cx="7" cy="7" r="2" fill="#207448" />
    <circle cx="14" cy="7" r="2" fill="#207448" />
    <text class="node-text" x="46" y="27">c2 (10.10.0.12)</text>
  </g>

  <!-- Node 4: uplink NIC -->
  <g transform="translate(1290, 188)">
    <rect x="0" y="4" width="38" height="30" rx="3" fill="none" stroke="#207448" stroke-width="3" />
    <line x1="7" y1="34" x2="7" y2="38" stroke="#207448" stroke-width="3" />
    <line x1="14" y1="34" x2="14" y2="38" stroke="#207448" stroke-width="3" />
    <line x1="21" y1="34" x2="21" y2="38" stroke="#207448" stroke-width="3" />
    <line x1="28" y1="34" x2="28" y2="38" stroke="#207448" stroke-width="3" />
    <text class="node-text" x="48" y="27">uplink NIC</text>
  </g>

  <!-- Lane 1: c1 to c2 on the same bridge -->
  <rect x="56" y="256" width="1488" height="200" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
  
  <!-- Lane 1 Header & Number Circle -->
  <circle cx="92" cy="288" r="24" fill="#207448" />
  <text class="circle-text" x="92" y="288">1</text>
  <text class="section-title" x="130" y="298">c1 to c2 on the same bridge</text>

  <!-- Lane 1 Arrow -->
  <line x1="610" y1="288" x2="1510" y2="288" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- Lane 1 Content -->
  <text class="body-text" x="76" y="334">c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves</text>
  <text class="body-text" x="76" y="360">c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame</text>
  <text class="body-text" x="76" y="386">to c2's veth and eth0</text>
  <text class="body-text" x="76" y="416">br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic;</text>
  <text class="body-text" x="76" y="442">Kubernetes requires it so kube-proxy rules apply</text>

  <!-- Lane 2: c1 to the Internet -->
  <rect x="56" y="476" width="1488" height="260" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />

  <!-- Lane 2 Header & Number Circle -->
  <circle cx="92" cy="508" r="24" fill="#207448" />
  <text class="circle-text" x="92" y="508">2</text>
  <text class="section-title" x="130" y="518">c1 to the Internet</text>

  <!-- Lane 2 Arrow -->
  <line x1="430" y1="508" x2="1510" y2="508" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />

  <!-- Lane 2 Content -->
  <text class="body-text" x="76" y="554">default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD</text>
  <text class="body-text" x="76" y="580">then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed</text>
  <text class="body-text" x="76" y="606">by conntrack and delivered back through the bridge; the outside world only talks to the host</text>
  <text class="mono-text" x="76" y="638">sysctl -w net.ipv4.ip_forward=1</text>
  <text class="mono-text" x="76" y="664">iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE</text>
  <text class="mono-text" x="76" y="690">iptables -I FORWARD -i br0 -j ACCEPT</text>
  <text class="mono-text" x="76" y="716">iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT</text>

  <!-- Lane 3: host:8080 to c1:80 (Orange) -->
  <rect x="56" y="756" width="1488" height="120" rx="8" fill="#e8f1ea" stroke="#db8129" stroke-width="2.5" />

  <!-- Lane 3 Header & Number Circle -->
  <circle cx="92" cy="788" r="24" fill="#db8129" />
  <text class="circle-text" x="92" y="788">3</text>
  <text class="section-title-orange" x="130" y="798">host:8080 to c1:80</text>

  <!-- Lane 3 Arrow (Orange) -->
  <line x1="1510" y1="788" x2="450" y2="788" stroke="#db8129" stroke-width="4" marker-end="url(#arrow-orange)" />

  <!-- Lane 3 Content -->
  <text class="mono-text" x="76" y="834">iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.10.0.11:80</text>
  <text class="mono-text" x="76" y="860">iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8080 -j DNAT ... for local clients</text>

  <!-- Footer Box (DNS & Docker Note) -->
  <rect x="40" y="932" width="1520" height="132" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
  <text class="mono-text" x="64" y="966">DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf</text>
  <text class="body-text" x="64" y="996">almost literally what the default bridge network does: docker0, a veth per container, an IPAM</text>
  <text class="body-text" x="64" y="1022">address from a private pool, a default route via the bridge, masquerade, DNAT for published ports,</text>
  <text class="body-text" x="64" y="1048">a bind-mounted /etc/resolv.conf</text>

  <!-- Bottom Takeaway Bar -->
  <rect x="40" y="1104" width="1520" height="56" rx="8" fill="#207448" />
  <text class="takeaway-text" x="800" y="1139">A container is only a namespace plus a cable</text>
</svg>
"""

with open("output.svg", "w") as f:
    f.write(svg_code.strip())

print("Successfully written output.svg")
