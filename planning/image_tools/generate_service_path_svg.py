import xml.etree.ElementTree as ET
import re

def generate_svg():
    lines = []
    def a(line):
        lines.append(line)

    a('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    a('  <title>The Kubernetes Service path: seven checks in order</title>')
    a('  <desc>When a Service fails, confirm in order: Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack.</desc>')
    a('')
    a('  <defs>')
    a('    <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">')
    a('      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#207448"/>')
    a('    </marker>')
    a('  </defs>')
    a('')
    a('  <!-- Background -->')
    a('  <rect width="1600" height="1200" fill="#f5f8f5"/>')
    a('')
    a('  <!-- Title -->')
    a('  <text x="800" y="88" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">When a Service fails, confirm in order</text>')
    a('')
    a('  <!-- Downward Arrow on Left Edge -->')
    a('  <line x1="100" y1="140" x2="100" y2="1064" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)"/>')
    a('  <text x="66" y="602" transform="rotate(-90 66 602)" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448" text-anchor="middle">read top to bottom</text>')
    a('')
    a('  <!-- Small Box on Right Side -->')
    a('  <rect x="1190" y="140" width="370" height="92" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    a('  <text x="1215" y="180" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
    a('    <tspan x="1215" dy="0">the first failing rung </tspan>')
    a('    <tspan x="1215" dy="28">is where to look</tspan>')
    a('  </text>')
    a('')

    # Outline Icons
    # Pod icon: two stacked container boxes
    pod_icon = '''<g transform="translate(236, 162)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="2" y="2" width="44" height="20" rx="4"/>
    <line x1="12" y1="2" x2="12" y2="22"/>
    <line x1="22" y1="2" x2="22" y2="22"/>
    <rect x="2" y="26" width="44" height="20" rx="4"/>
    <line x1="12" y1="26" x2="12" y2="46"/>
    <line x1="22" y1="26" x2="22" y2="46"/>
  </g>'''

    # Service icon: network hub
    service_icon = '''<g transform="translate(236, 296)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="24" cy="24" r="10"/>
    <circle cx="24" cy="6" r="4" fill="#207448"/>
    <line x1="24" y1="14" x2="24" y2="10"/>
    <circle cx="24" cy="42" r="4" fill="#207448"/>
    <line x1="24" y1="34" x2="24" y2="38"/>
    <circle cx="6" cy="24" r="4" fill="#207448"/>
    <line x1="14" y1="24" x2="10" y2="24"/>
    <circle cx="42" cy="24" r="4" fill="#207448"/>
    <line x1="34" y1="24" x2="38" y2="24"/>
  </g>'''

    # DNS icon: globe
    dns_icon = '''<g transform="translate(236, 430)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="24" cy="24" r="21"/>
    <line x1="3" y1="24" x2="45" y2="24"/>
    <ellipse cx="24" cy="24" rx="10" ry="21"/>
    <line x1="24" y1="3" x2="24" y2="45"/>
  </g>'''

    # Endpoints icon: network branches
    endpoints_icon = '''<g transform="translate(236, 578)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <circle cx="10" cy="24" r="6" fill="#207448"/>
    <line x1="16" y1="24" x2="28" y2="24"/>
    <path d="M 28 10 V 38"/>
    <line x1="28" y1="10" x2="38" y2="10"/>
    <circle cx="42" cy="10" r="5"/>
    <line x1="28" y1="24" x2="38" y2="24"/>
    <circle cx="42" cy="24" r="5"/>
    <line x1="28" y1="38" x2="38" y2="38"/>
    <circle cx="42" cy="38" r="5"/>
  </g>'''

    # Ports icon: ethernet port / plug
    ports_icon = '''<g transform="translate(236, 726)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="40" height="36" rx="6"/>
    <line x1="12" y1="14" x2="12" y2="26"/>
    <line x1="20" y1="14" x2="20" y2="26"/>
    <line x1="28" y1="14" x2="28" y2="26"/>
    <line x1="36" y1="14" x2="36" y2="26"/>
    <path d="M 16 42 V 46 H 32 V 42"/>
  </g>'''

    # Kube-proxy rules icon: firewall / rules matrix
    rules_icon = '''<g transform="translate(236, 860)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="40" height="36" rx="4"/>
    <line x1="4" y1="18" x2="44" y2="18"/>
    <line x1="4" y1="30" x2="44" y2="30"/>
    <line x1="18" y1="6" x2="18" y2="18"/>
    <line x1="30" y1="6" x2="30" y2="18"/>
    <line x1="12" y1="18" x2="12" y2="30"/>
    <line x1="26" y1="18" x2="26" y2="30"/>
    <line x1="38" y1="18" x2="38" y2="30"/>
    <line x1="20" y1="30" x2="20" y2="42"/>
    <line x1="32" y1="30" x2="32" y2="42"/>
  </g>'''

    # Conntrack icon: table hash slots
    conntrack_icon = '''<g transform="translate(236, 994)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <rect x="4" y="6" width="40" height="36" rx="4"/>
    <line x1="4" y1="18" x2="44" y2="18"/>
    <line x1="4" y1="30" x2="44" y2="30"/>
    <line x1="16" y1="6" x2="16" y2="42"/>
    <circle cx="10" cy="12" r="2.5" fill="#207448"/>
    <circle cx="10" cy="24" r="2.5" fill="#207448"/>
    <circle cx="10" cy="36" r="2.5" fill="#207448"/>
    <line x1="22" y1="12" x2="38" y2="12"/>
    <line x1="22" y1="24" x2="38" y2="24"/>
    <line x1="22" y1="36" x2="38" y2="36"/>
  </g>'''

    # Rung 1
    a('  <!-- Rung 1: Pod -->')
    a('  <rect x="160" y="140" width="990" height="92" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    a('  <circle cx="196" cy="186" r="24" fill="#207448"/>')
    a('  <text x="196" y="195" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>')
    a(f'  {pod_icon}')
    a('  <text x="325" y="181" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Pod</text>')
    a('  <text x="325" y="211" font-family="monospace" font-size="24" fill="#303a36">call the pod IP and pod port directly from another pod</text>')
    a('')

    # Rung 2
    a('  <!-- Rung 2: Service -->')
    a('  <rect x="160" y="274" width="1400" height="92" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    a('  <circle cx="196" cy="320" r="24" fill="#207448"/>')
    a('  <text x="196" y="329" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>')
    a(f'  {service_icon}')
    a('  <text x="325" y="315" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Service</text>')
    a('  <text x="325" y="345" font-family="monospace" font-size="24" fill="#303a36">the Service exists, otherwise lookup fails with Name or service not known</text>')
    a('')

    # Rung 3
    a('  <!-- Rung 3: DNS -->')
    a('  <rect x="160" y="408" width="1400" height="92" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    a('  <circle cx="196" cy="454" r="24" fill="#207448"/>')
    a('  <text x="196" y="463" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">3</text>')
    a(f'  {dns_icon}')
    a('  <text x="325" y="449" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">DNS</text>')
    a('  <text x="325" y="479" font-family="monospace" font-size="24" fill="#303a36">short, namespaced and full names resolve</text>')
    a('')

    # Rung 4
    a('  <!-- Rung 4: Endpoints -->')
    a('  <rect x="160" y="542" width="780" height="120" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    a('  <circle cx="196" cy="602" r="24" fill="#207448"/>')
    a('  <text x="196" y="611" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">4</text>')
    a(f'  {endpoints_icon}')
    a('  <text x="325" y="583" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Endpoints</text>')
    a('  <text x="325" y="611" font-family="monospace" font-size="24" fill="#303a36">')
    a('    <tspan x="325" dy="0">kubectl get endpointslices </tspan>')
    a('    <tspan x="325" dy="27">-l kubernetes.io/service-name=hostnames</tspan>')
    a('  </text>')
    a('')

    # Orange Callout beside Rung 4
    a('  <!-- Orange Callout beside Rung 4 -->')
    a('  <rect x="980" y="542" width="580" height="120" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="3"/>')
    a('  <text x="1010" y="580" font-family="sans-serif" font-size="24" fill="#303a36">')
    a('    <tspan x="1010" dy="0">ENDPOINTS shows none means </tspan>')
    a('    <tspan x="1010" dy="28">the Service selector does not </tspan>')
    a('    <tspan x="1010" dy="28">match pod labels</tspan>')
    a('  </text>')
    a('')

    # Rung 5
    a('  <!-- Rung 5: Ports -->')
    a('  <rect x="160" y="704" width="1400" height="92" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    a('  <circle cx="196" cy="750" r="24" fill="#207448"/>')
    a('  <text x="196" y="759" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">5</text>')
    a(f'  {ports_icon}')
    a('  <text x="325" y="745" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Ports</text>')
    a('  <text x="325" y="775" font-family="monospace" font-size="24" fill="#303a36">Service port listed, targetPort correct, named port matched</text>')
    a('')

    # Rung 6
    a('  <!-- Rung 6: kube-proxy rules -->')
    a('  <rect x="160" y="838" width="1400" height="92" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    a('  <circle cx="196" cy="884" r="24" fill="#207448"/>')
    a('  <text x="196" y="893" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">6</text>')
    a(f'  {rules_icon}')
    a('  <text x="325" y="879" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">kube-proxy rules</text>')
    a('  <text x="325" y="909" font-family="monospace" font-size="24" fill="#303a36">iptables-save grep hostnames, or ipvsadm -ln</text>')
    a('')

    # Rung 7
    a('  <!-- Rung 7: Conntrack -->')
    a('  <rect x="160" y="972" width="1400" height="92" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>')
    a('  <circle cx="196" cy="1018" r="24" fill="#207448"/>')
    a('  <text x="196" y="1027" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">7</text>')
    a(f'  {conntrack_icon}')
    a('  <text x="325" y="1013" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Conntrack</text>')
    a('  <text x="325" y="1043" font-family="monospace" font-size="24" fill="#303a36">table usage, since iptables Service load balancing depends on connection tracking</text>')
    a('')

    # Green Takeaway Bar
    a('  <!-- Green Takeaway Bar -->')
    a('  <rect x="40" y="1104" width="1520" height="56" rx="12" fill="#207448"/>')
    a('  <text x="800" y="1139.2" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack</text>')
    a('</svg>')

    return "\n".join(lines)

if __name__ == "__main__":
    svg_content = generate_svg()
    with open("service_path_candidate.svg", "w") as f:
        f.write(svg_content)
    print("Generated service_path_candidate.svg successfully!")
