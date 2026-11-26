import re
import pathlib

def generate():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>kube-proxy iptables mode: a random pick per connection, with no view of load</title>
  <desc>Infographic explaining kube-proxy iptables random probability chain per connection, service types, implementation options, supporting components, and long-lived gRPC considerations.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- ==================== HEADER: TITLE ==================== -->
  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">kube-proxy iptables mode: </tspan>
    <tspan x="800" dy="54">a random pick per connection, with no view of load</tspan>
  </text>

  <!-- ==================== SECTION 1: TOP ROW (y=130..290, h=160) ==================== -->

  <!-- Top Left: Service Types (w=700, x=40..740) -->
  <g id="box-service-types">
    <rect x="40" y="130" width="700" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Network Hub / Service Icon (56x56) -->
    <g transform="translate(64, 182)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
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
    <text x="142" y="176" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="142" dy="0">Kubernetes service types:</tspan>
      <tspan x="142" dy="30">ClusterIP, NodePort, LoadBalancer,</tspan>
      <tspan x="142" dy="30">Headless give a stable virtual IP</tspan>
    </text>
  </g>

  <!-- Top Right: Implementation Options (w=780, x=780..1560) -->
  <g id="box-impl-options">
    <rect x="780" y="130" width="780" height="160" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <rect x="780" y="130" width="780" height="46" rx="14" fill="#e8f1ea" />
    <line x1="780" y1="176" x2="1560" y2="176" stroke="#207448" stroke-width="1.5" />

    <!-- Gear / Config Icon (32x32) in header -->
    <g transform="translate(798, 137)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="16" cy="16" r="6" fill="#ffffff" />
      <path d="M16 4 v4 M16 24 v4 M4 16 h4 M24 16 h4 M7.5 7.5 l2.8 2.8 M21.7 21.7 l2.8 2.8 M7.5 24.5 l2.8 -2.8 M21.7 10.3 l2.8 -2.8" />
    </g>
    <text x="842" y="162" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Implementation options</text>

    <!-- 3 Implementation chips/rows -->
    <text x="806" y="206" font-family="sans-serif" font-size="24" fill="#303a36">iptables rules (random probability chain)</text>
    <text x="806" y="238" font-family="sans-serif" font-size="24" fill="#303a36">IPVS (a real L4 scheduler)</text>
    <text x="806" y="270" font-family="sans-serif" font-size="24" fill="#303a36">eBPF replacement such as Cilium</text>
  </g>

  <!-- ==================== SECTION 2: MIDDLE (y=330..710, h=380) ==================== -->

  <!-- Left: A chain of rules for a Service with N pods (w=940, x=40..980) -->
  <g id="box-rule-chain">
    <rect x="40" y="330" width="940" height="380" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <rect x="40" y="330" width="940" height="52" rx="14" fill="#e8f1ea" />
    <line x1="40" y1="382" x2="980" y2="382" stroke="#207448" stroke-width="1.5" />

    <!-- List Icon in header -->
    <g transform="translate(58, 340)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="24" height="24" rx="4" fill="#ffffff" />
      <line x1="9" y1="10" x2="23" y2="10" />
      <line x1="9" y1="16" x2="23" y2="16" />
      <line x1="9" y1="22" x2="18" y2="22" />
    </g>
    <text x="510" y="366" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">A chain of rules for a Service with N pods</text>

    <!-- Rule 1 Row (y=394..454, h=60) -->
    <g id="row-rule-1">
      <rect x="58" y="394" width="904" height="60" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <g transform="translate(70, 403)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="21" r="8" fill="#e8f1ea" />
        <path d="M21 5 v5 M21 32 v5 M5 21 h5 M32 21 h5 M9.7 9.7 l3.5 3.5 M28.8 28.8 l3.5 3.5 M9.7 32.3 l3.5 -3.5 M28.8 13.2 l3.5 -3.5" />
      </g>
      <text x="124" y="436" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Rule 1</text>
      <text x="230" y="436" font-family="sans-serif" font-size="24" fill="#303a36">match with probability 1/N, else fall through</text>
    </g>

    <!-- Rule 2 Row (y=462..522, h=60) -->
    <g id="row-rule-2">
      <rect x="58" y="462" width="904" height="60" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <g transform="translate(70, 471)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="21" r="8" fill="#e8f1ea" />
        <path d="M21 5 v5 M21 32 v5 M5 21 h5 M32 21 h5 M9.7 9.7 l3.5 3.5 M28.8 28.8 l3.5 3.5 M9.7 32.3 l3.5 -3.5 M28.8 13.2 l3.5 -3.5" />
      </g>
      <text x="124" y="504" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">rule 2</text>
      <text x="230" y="504" font-family="sans-serif" font-size="24" fill="#303a36">match with probability 1/(N-1), else fall through</text>
    </g>

    <!-- Rule 3 Row (y=530..590, h=60) -->
    <g id="row-rule-3">
      <rect x="58" y="530" width="904" height="60" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <g transform="translate(70, 539)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="21" r="8" fill="#e8f1ea" />
        <path d="M21 5 v5 M21 32 v5 M5 21 h5 M32 21 h5 M9.7 9.7 l3.5 3.5 M28.8 28.8 l3.5 3.5 M9.7 32.3 l3.5 -3.5 M28.8 13.2 l3.5 -3.5" />
      </g>
      <text x="124" y="572" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">rule 3</text>
      <text x="230" y="572" font-family="sans-serif" font-size="24" fill="#303a36">match with probability 1/(N-2)</text>
    </g>

    <!-- Ellipsis Row (y=596..624) -->
    <g id="row-ellipsis">
      <text x="510" y="622" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">...</text>
    </g>

    <!-- Last Rule Row (y=632..692, h=60) -->
    <g id="row-last-rule">
      <rect x="58" y="632" width="904" height="60" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <g transform="translate(70, 641)" stroke="#207448" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="21" cy="21" r="14" fill="#e8f1ea" />
        <polyline points="14 21 19 26 28 16" />
      </g>
      <text x="124" y="674" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">last rule</text>
      <text x="260" y="674" font-family="sans-serif" font-size="24" fill="#303a36">match always</text>
    </g>
  </g>

  <!-- Right: Two Cards (w=540, x=1020..1560) -->

  <!-- Right Card 1: Decision characteristics (y=330..480, h=150) -->
  <g id="card-decision-random">
    <rect x="1020" y="330" width="540" height="150" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <!-- Die / Dice Random Icon (56x56) -->
    <g transform="translate(1042, 377)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="6" width="44" height="44" rx="8" fill="#e8f1ea" />
      <circle cx="20" cy="20" r="3" fill="#207448" />
      <circle cx="36" cy="20" r="3" fill="#207448" />
      <circle cx="28" cy="28" r="3" fill="#207448" />
      <circle cx="20" cy="36" r="3" fill="#207448" />
      <circle cx="36" cy="36" r="3" fill="#207448" />
    </g>
    <text x="1118" y="375" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1118" dy="0">each decision is random and</tspan>
      <tspan x="1118" dy="30">made per connection, with no</tspan>
      <tspan x="1118" dy="30">view of how busy each pod is</tspan>
    </text>
  </g>

  <!-- Right Card 2: Orange Outcome (y=520..710, h=190) -->
  <g id="card-orange-outcome">
    <rect x="1020" y="520" width="540" height="190" rx="14" fill="#fffaf5" stroke="#db8129" stroke-width="3" />
    <!-- Alert / Warning Icon (56x56) in Orange -->
    <g transform="translate(1042, 587)" stroke="#db8129" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M28 6 L50 46 L6 46 Z" fill="#fff2e5" />
      <line x1="28" y1="20" x2="28" y2="32" />
      <circle cx="28" cy="40" r="2.5" fill="#db8129" />
    </g>
    <text x="1118" y="572" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1118" dy="0">a slow pod still gets its</tspan>
      <tspan x="1118" dy="30">random share, and a gRPC</tspan>
      <tspan x="1118" dy="30">channel that picked it stays</tspan>
      <tspan x="1118" dy="30">there for its whole life</tspan>
    </text>
  </g>

  <!-- ==================== SECTION 3: SUPPORTING PIECES (y=750..1050, h=300) ==================== -->
  <g id="box-supporting-pieces">
    <rect x="40" y="750" width="1520" height="300" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <rect x="40" y="750" width="1520" height="46" rx="14" fill="#e8f1ea" />
    <line x1="40" y1="796" x2="1560" y2="796" stroke="#207448" stroke-width="1.5" />

    <!-- Modules / Extension Icon (32x32) in header -->
    <g transform="translate(58, 757)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="4" width="10" height="10" rx="2" fill="#ffffff" />
      <rect x="18" y="4" width="10" height="10" rx="2" fill="#ffffff" />
      <rect x="4" y="18" width="10" height="10" rx="2" fill="#ffffff" />
      <rect x="18" y="18" width="10" height="10" rx="2" fill="#ffffff" />
    </g>
    <text x="800" y="782" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">Supporting pieces</text>

    <!-- Card 1: EndpointSlices (w=700, x=65..765, y=810..905, h=95) -->
    <g id="card-sp-endpointslices">
      <rect x="65" y="810" width="700" height="95" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <text x="415" y="850" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="415" dy="0">EndpointSlices list the ready pods and</tspan>
        <tspan x="415" dy="30">readiness probes control membership</tspan>
      </text>
    </g>

    <!-- Card 2: Service Meshes (w=700, x=835..1535, y=810..905, h=95) -->
    <g id="card-sp-meshes">
      <rect x="835" y="810" width="700" height="95" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <text x="1185" y="850" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1185" dy="0">service meshes add per-pod proxies for mTLS,</tspan>
        <tspan x="1185" dy="30">retries and L7 balancing between services</tspan>
      </text>
    </g>

    <!-- Card 3: Ingress & Gateway API (w=700, x=65..765, y=918..1038, h=120) -->
    <g id="card-sp-ingress">
      <rect x="65" y="918" width="700" height="120" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <text x="415" y="958" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="415" dy="0">Ingress and Gateway API: L7 HTTP routing and</tspan>
        <tspan x="415" dy="28">TLS through nginx, HAProxy, Contour, Emissary,</tspan>
        <tspan x="415" dy="28">Envoy Gateway, Traefik and cloud controllers</tspan>
      </text>
    </g>

    <!-- Card 4: MetalLB & VIPs (w=700, x=835..1535, y=918..1038, h=120) -->
    <g id="card-sp-metallb">
      <rect x="835" y="918" width="700" height="120" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />
      <text x="1185" y="958" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
        <tspan x="1185" dy="0">MetalLB, kube-vip and Cilium provide</tspan>
        <tspan x="1185" dy="28">LoadBalancer VIPs on bare metal using</tspan>
        <tspan x="1185" dy="28">ARP or BGP (ECMP)</tspan>
      </text>
    </g>
  </g>

  <!-- ==================== SECTION 4: TAKEAWAY BAR (y=1090..1155, h=65) ==================== -->
  <g id="bar-takeaway">
    <rect x="40" y="1090" width="1520" height="65" rx="12" fill="#207448" />
    <!-- Check / Target Icon in white -->
    <g transform="translate(62, 1098)" stroke="#ffffff" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="24" cy="24" r="16" />
      <polyline points="16 24 22 30 32 18" />
    </g>
    <text x="800" y="1132" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Long-lived gRPC connections need L7 or client-side balancing to spread load evenly</text>
  </g>
</svg>'''
    pathlib.Path("kube_proxy_iptables.svg").write_text(svg, encoding="utf-8")
    print("Regenerated kube_proxy_iptables.svg")

generate()
