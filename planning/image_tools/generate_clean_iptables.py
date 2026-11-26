import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>kube-proxy iptables mode: a random pick per connection, with no view of load</title>
  <desc>Visual infographic explaining how kube-proxy in iptables mode uses a random probability chain per connection without load awareness.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- ==================== HEADER: TITLE ==================== -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">kube-proxy iptables mode: </tspan>
    <tspan x="800" dy="54">a random pick per connection, with no view of load</tspan>
  </text>

  <!-- ==================== SECTION 1: TOP ROW (y=126..328) ==================== -->

  <!-- Top Left: Kubernetes Service Types (w=720, x=40..760) -->
  <g id="box-service-types">
    <rect x="40" y="126" width="720" height="202" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Network Hub / Service Icon (56x56) -->
    <g transform="translate(64, 199)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10" fill="#e8f1ea" />
      <circle cx="10" cy="12" r="6" fill="#ffffff" />
      <circle cx="46" cy="12" r="6" fill="#ffffff" />
      <circle cx="10" cy="44" r="6" fill="#ffffff" />
      <circle cx="46" cy="44" r="6" fill="#ffffff" />
      <line x1="16" y1="16" x2="22" y2="22" />
      <line x1="40" y1="16" x2="34" y2="22" />
      <line x1="16" y1="40" x2="22" y2="34" />
      <line x1="40" y1="40" x2="34" y2="34" />
    </g>
    <text x="144" y="186" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="144" dy="0">Kubernetes service types: </tspan>
      <tspan x="144" dy="32">ClusterIP, NodePort, LoadBalancer, </tspan>
      <tspan x="144" dy="32">Headless give a stable virtual IP</tspan>
    </text>
  </g>

  <!-- Top Right: Implementation Options (w=760, x=800..1560) -->
  <g id="box-impl-options">
    <rect x="800" y="126" width="760" height="202" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Option 1: iptables rules -->
    <rect x="820" y="136" width="720" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="1180" y="171" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">iptables rules (random probability chain)</text>

    <!-- Option 2: IPVS -->
    <rect x="820" y="200" width="720" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="1180" y="235" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">IPVS (a real L4 scheduler)</text>

    <!-- Option 3: eBPF / Cilium -->
    <rect x="820" y="264" width="720" height="56" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />
    <text x="1180" y="299" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">eBPF replacement such as Cilium</text>
  </g>

  <!-- ==================== SECTION 2: MIDDLE (y=344..724) ==================== -->

  <!-- Left: Vertical chain of rules for a Service with N pods (w=940, x=40..980) -->
  <g id="box-rule-chain">
    <rect x="40" y="344" width="940" height="376" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

    <!-- Rule 1 Row -->
    <g id="row-rule-1">
      <rect x="60" y="360" width="900" height="64" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <g transform="translate(74, 370)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="21" r="8" fill="#e8f1ea" />
        <path d="M21 5 v5 M21 32 v5 M5 21 h5 M32 21 h5 M9.7 9.7 l3.5 3.5 M28.8 28.8 l3.5 3.5 M9.7 32.3 l3.5 -3.5 M28.8 13.2 l3.5 -3.5" />
      </g>
      <text x="140" y="400" font-family="sans-serif" font-size="24" fill="#303a36">match with probability 1/N, else fall through</text>
    </g>

    <!-- Rule 2 Row -->
    <g id="row-rule-2">
      <rect x="60" y="436" width="900" height="64" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <g transform="translate(74, 446)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="21" r="8" fill="#e8f1ea" />
        <path d="M21 5 v5 M21 32 v5 M5 21 h5 M32 21 h5 M9.7 9.7 l3.5 3.5 M28.8 28.8 l3.5 3.5 M9.7 32.3 l3.5 -3.5 M28.8 13.2 l3.5 -3.5" />
      </g>
      <text x="140" y="476" font-family="sans-serif" font-size="24" fill="#303a36">match with probability 1/(N-1), else fall through</text>
    </g>

    <!-- Rule 3 Row -->
    <g id="row-rule-3">
      <rect x="60" y="512" width="900" height="64" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <g transform="translate(74, 522)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="21" r="8" fill="#e8f1ea" />
        <path d="M21 5 v5 M21 32 v5 M5 21 h5 M32 21 h5 M9.7 9.7 l3.5 3.5 M28.8 28.8 l3.5 3.5 M9.7 32.3 l3.5 -3.5 M28.8 13.2 l3.5 -3.5" />
      </g>
      <text x="140" y="552" font-family="sans-serif" font-size="24" fill="#303a36">match with probability 1/(N-2)</text>
    </g>

    <!-- Visual Ellipsis (SVG circles, NOT text) -->
    <g id="row-ellipsis" fill="#207448">
      <circle cx="490" cy="604" r="5" />
      <circle cx="510" cy="604" r="5" />
      <circle cx="530" cy="604" r="5" />
    </g>

    <!-- Last Rule Row -->
    <g id="row-last-rule">
      <rect x="60" y="638" width="900" height="64" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <g transform="translate(74, 648)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="21" r="14" fill="#e8f1ea" />
        <polyline points="14 21 19 26 28 16" />
      </g>
      <text x="140" y="678" font-family="sans-serif" font-size="24" fill="#303a36">match always</text>
    </g>
  </g>

  <!-- Right: Two Cards (w=540, x=1020..1560) -->

  <!-- Right Card 1: Decision characteristics (y=344..504, h=160) -->
  <g id="card-decision-random">
    <rect x="1020" y="344" width="540" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Die / Dice Random Icon (56x56) -->
    <g transform="translate(1042, 396)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="44" rx="8" fill="#e8f1ea" />
      <circle cx="20" cy="20" r="3" fill="#207448" />
      <circle cx="36" cy="20" r="3" fill="#207448" />
      <circle cx="28" cy="28" r="3" fill="#207448" />
      <circle cx="20" cy="36" r="3" fill="#207448" />
      <circle cx="36" cy="36" r="3" fill="#207448" />
    </g>
    <text x="1120" y="395" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1120" dy="0">each decision is random and </tspan>
      <tspan x="1120" dy="32">made per connection, with no </tspan>
      <tspan x="1120" dy="32">view of how busy each pod is</tspan>
    </text>
  </g>

  <!-- Right Card 2: Orange Outcome (y=544..724, h=180) -->
  <g id="card-orange-outcome">
    <rect x="1020" y="544" width="540" height="180" rx="14" fill="#fffaf5" stroke="#db8129" stroke-width="3" />
    <!-- Alert / Warning Icon (56x56) in Orange -->
    <g transform="translate(1042, 606)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M28 6 L50 46 L6 46 Z" fill="#fff2e5" />
      <line x1="28" y1="20" x2="28" y2="32" />
      <circle cx="28" cy="40" r="2.5" fill="#db8129" />
    </g>
    <text x="1120" y="592" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1120" dy="0">a slow pod still gets its </tspan>
      <tspan x="1120" dy="30">random share, and a gRPC </tspan>
      <tspan x="1120" dy="30">channel that picked it stays </tspan>
      <tspan x="1120" dy="30">there for its whole life</tspan>
    </text>
  </g>

  <!-- ==================== SECTION 3: SUPPORTING PIECES (y=764..1074, h=310) ==================== -->
  <g id="box-supporting-pieces">
    <rect x="40" y="764" width="1520" height="310" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />

    <!-- Card 1: EndpointSlices (w=705, x=65..770, y=784..899, h=115) -->
    <g id="card-sp-endpointslices">
      <rect x="65" y="784" width="705" height="115" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <text x="417" y="834" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="417" dy="0">EndpointSlices list the ready pods and </tspan>
        <tspan x="417" dy="32">readiness probes control membership</tspan>
      </text>
    </g>

    <!-- Card 2: Service Meshes (w=705, x=830..1535, y=784..899, h=115) -->
    <g id="card-sp-meshes">
      <rect x="830" y="784" width="705" height="115" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <text x="1182" y="824" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1182" dy="0">service meshes add per-pod proxies for </tspan>
        <tspan x="1182" dy="28">mTLS, retries and L7 balancing </tspan>
        <tspan x="1182" dy="28">between services</tspan>
      </text>
    </g>

    <!-- Card 3: Ingress & Gateway API (w=705, x=65..770, y=919..1054, h=135) -->
    <g id="card-sp-ingress">
      <rect x="65" y="919" width="705" height="135" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <text x="417" y="954" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="417" dy="0">Ingress and Gateway API: L7 HTTP routing </tspan>
        <tspan x="417" dy="26">and TLS through nginx, HAProxy, Contour, </tspan>
        <tspan x="417" dy="26">Emissary, Envoy Gateway, Traefik and </tspan>
        <tspan x="417" dy="26">cloud controllers</tspan>
      </text>
    </g>

    <!-- Card 4: MetalLB & VIPs (w=705, x=830..1535, y=919..1054, h=135) -->
    <g id="card-sp-metallb">
      <rect x="830" y="919" width="705" height="135" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <text x="1182" y="964" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1182" dy="0">MetalLB, kube-vip and Cilium provide </tspan>
        <tspan x="1182" dy="30">LoadBalancer VIPs on bare metal </tspan>
        <tspan x="1182" dy="30">using ARP or BGP (ECMP)</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== SECTION 4: TAKEAWAY BAR (y=1105..1170, h=65) ==================== -->
  <g id="bar-takeaway">
    <rect x="40" y="1105" width="1520" height="65" rx="12" fill="#207448" />
    <!-- Check / Target Icon in white (40x40) -->
    <g transform="translate(62, 1117)" stroke="#ffffff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="20" cy="20" r="15" />
      <polyline points="13 20 18 25 27 15" />
    </g>
    <text x="800" y="1146" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Long-lived gRPC connections need L7 or client-side balancing to spread load evenly</text>
  </g>
</svg>'''

pathlib.Path("test_clean_iptables.svg").write_text(svg_content, encoding="utf-8")
print("Wrote test_clean_iptables.svg")
