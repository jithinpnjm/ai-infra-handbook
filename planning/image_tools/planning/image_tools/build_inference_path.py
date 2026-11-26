import xml.etree.ElementTree as ET
import re
import pathlib

def generate_svg():
    svg_lines = []
    svg_lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg_lines.append('  <title>The whiteboard path for an inference service, and the metrics to watch on it</title>')
    svg_lines.append('  <desc>Whiteboard path for an inference service across gateways, L7 router, endpoint picker, inference pods, metrics, streaming hygiene, and L4 scaling.</desc>')
    
    # Defs
    svg_lines.append('  <defs>')
    svg_lines.append('    <marker id="arrow" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg_lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg_lines.append('    </marker>')
    svg_lines.append('  </defs>')
    
    # Background
    svg_lines.append('  <!-- Canvas Background -->')
    svg_lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    
    # Title (48px bold)
    svg_lines.append('  <!-- Title -->')
    svg_lines.append('  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg_lines.append('    <tspan x="800" dy="0">The whiteboard path for an inference service,</tspan>')
    svg_lines.append('    <tspan x="800" dy="50">and the metrics to watch on it</tspan>')
    svg_lines.append('  </text>')
    
    # ==================== ARCHITECTURE PIPELINE ====================
    # Node 1: Client
    svg_lines.append('  <!-- Node 1: Client -->')
    svg_lines.append('  <g id="node-client">')
    svg_lines.append('    <rect x="40" y="125" width="150" height="120" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: Client Desktop/Screen (56x40) at (87, 137)
    svg_lines.append('    <g transform="translate(87, 137)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('      <rect x="4" y="4" width="48" height="32" rx="4" fill="#ffffff" />')
    svg_lines.append('      <line x1="28" y1="36" x2="28" y2="44" />')
    svg_lines.append('      <line x1="16" y1="44" x2="40" y2="44" />')
    svg_lines.append('    </g>')
    svg_lines.append('    <text x="115" y="222" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Client</text>')
    svg_lines.append('  </g>')
    
    # Arrow 1: Hop 1 from Node 1 to Node 2
    svg_lines.append('  <!-- Hop 1: Client to Gateway -->')
    svg_lines.append('  <line x1="190" y1="185" x2="400" y2="185" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />')
    
    # Orange marker on first hop
    svg_lines.append('  <circle cx="295" cy="185" r="7" fill="#db8129" stroke="#ffffff" stroke-width="2" />')
    svg_lines.append('  <line x1="295" y1="192" x2="295" y2="255" stroke="#db8129" stroke-width="2" stroke-dasharray="4 4" />')
    
    # Annotation on the first hop
    svg_lines.append('  <!-- Annotation on first hop -->')
    svg_lines.append('  <g id="annotation-hop1">')
    svg_lines.append('    <rect x="50" y="255" width="330" height="135" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="2" />')
    svg_lines.append('    <text x="215" y="284" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">')
    svg_lines.append('      <tspan x="215" dy="0">where pinning</tspan>')
    svg_lines.append('      <tspan x="215" dy="28">happens at L4</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('    <line x1="70" y1="324" x2="360" y2="324" stroke="#e8f1ea" stroke-width="1.5" />')
    svg_lines.append('    <text x="215" y="352" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_lines.append('      <tspan x="215" dy="0">L7 or client-side</tspan>')
    svg_lines.append('      <tspan x="215" dy="28">balancing fixes it</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')
    
    # Node 2: Gateway
    svg_lines.append('  <!-- Node 2: Gateways -->')
    svg_lines.append('  <g id="node-gateway">')
    svg_lines.append('    <rect x="400" y="125" width="275" height="265" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: Network Gateway / Router at (510, 137)
    svg_lines.append('    <g transform="translate(510, 137)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('      <rect x="4" y="6" width="48" height="26" rx="4" fill="#ffffff" />')
    svg_lines.append('      <circle cx="16" cy="19" r="3" fill="#207448" />')
    svg_lines.append('      <circle cx="28" cy="19" r="3" fill="#207448" />')
    svg_lines.append('      <circle cx="40" cy="19" r="3" fill="#207448" />')
    svg_lines.append('      <line x1="12" y1="32" x2="8" y2="44" />')
    svg_lines.append('      <line x1="44" y1="32" x2="48" y2="44" />')
    svg_lines.append('    </g>')
    svg_lines.append('    <text x="537" y="224" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg_lines.append('      <tspan x="537" dy="0">anycast or ECMP</tspan>')
    svg_lines.append('      <tspan x="537" dy="32">to a fleet of L4</tspan>')
    svg_lines.append('      <tspan x="537" dy="32">and L7 gateways</tspan>')
    svg_lines.append('      <tspan x="537" dy="32">(BGP VIP, BFD)</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')
    
    # Arrow 2: Gateway to TLS/L7
    svg_lines.append('  <!-- Hop 2: Gateway to TLS Routing -->')
    svg_lines.append('  <line x1="675" y1="250" x2="705" y2="250" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />')
    
    # Node 3: TLS termination and L7 routing
    svg_lines.append('  <!-- Node 3: TLS Routing -->')
    svg_lines.append('  <g id="node-tls">')
    svg_lines.append('    <rect x="705" y="125" width="285" height="265" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: Shield / Lock at (820, 137)
    svg_lines.append('    <g transform="translate(820, 137)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('      <path d="M 8 10 L 28 4 L 48 10 C 48 28 28 42 28 42 C 28 42 8 28 8 10 Z" fill="#ffffff" />')
    svg_lines.append('      <circle cx="28" cy="22" r="4" fill="#207448" />')
    svg_lines.append('      <line x1="28" y1="26" x2="28" y2="32" stroke="#207448" stroke-width="3" />')
    svg_lines.append('    </g>')
    svg_lines.append('    <text x="847" y="224" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg_lines.append('      <tspan x="847" dy="0">TLS termination</tspan>')
    svg_lines.append('      <tspan x="847" dy="32">and L7 routing</tspan>')
    svg_lines.append('      <tspan x="847" dy="32">with per-request,</tspan>')
    svg_lines.append('      <tspan x="847" dy="32">per-tenant policy</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')
    
    # Arrow 3: TLS/L7 to Picker
    svg_lines.append('  <!-- Hop 3: TLS to Picker -->')
    svg_lines.append('  <line x1="990" y1="250" x2="1020" y2="250" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />')
    
    # Node 4: Endpoint picker
    svg_lines.append('  <!-- Node 4: Endpoint Picker -->')
    svg_lines.append('  <g id="node-picker">')
    svg_lines.append('    <rect x="1020" y="125" width="250" height="265" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: Scale / Picker / Balance at (1117, 137)
    svg_lines.append('    <g transform="translate(1117, 137)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('      <line x1="28" y1="6" x2="28" y2="42" />')
    svg_lines.append('      <line x1="8" y1="16" x2="48" y2="16" />')
    svg_lines.append('      <path d="M 8 16 L 3 32 H 17 Z" fill="#ffffff" />')
    svg_lines.append('      <path d="M 48 16 L 43 32 H 57 Z" fill="#ffffff" />')
    svg_lines.append('      <line x1="16" y1="42" x2="40" y2="42" />')
    svg_lines.append('    </g>')
    svg_lines.append('    <text x="1145" y="235" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg_lines.append('      <tspan x="1145" dy="0">load- and</tspan>')
    svg_lines.append('      <tspan x="1145" dy="34">cache-aware</tspan>')
    svg_lines.append('      <tspan x="1145" dy="34">endpoint picker</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')
    
    # Arrow 4: Picker to Pods
    svg_lines.append('  <!-- Hop 4: Picker to Inference Pods -->')
    svg_lines.append('  <line x1="1270" y1="250" x2="1300" y2="250" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow)" />')
    
    # Node 5: Inference pods
    svg_lines.append('  <!-- Node 5: Inference Pods -->')
    svg_lines.append('  <g id="node-pods">')
    svg_lines.append('    <rect x="1300" y="125" width="260" height="265" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: GPU Pod Cluster at (1402, 137)
    svg_lines.append('    <g transform="translate(1402, 137)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('      <rect x="6" y="6" width="44" height="34" rx="5" fill="#ffffff" />')
    svg_lines.append('      <line x1="16" y1="16" x2="24" y2="16" />')
    svg_lines.append('      <line x1="16" y1="24" x2="24" y2="24" />')
    svg_lines.append('      <line x1="16" y1="32" x2="24" y2="32" />')
    svg_lines.append('      <circle cx="38" cy="18" r="3" fill="#207448" />')
    svg_lines.append('      <circle cx="38" cy="28" r="3" fill="#207448" />')
    svg_lines.append('    </g>')
    svg_lines.append('    <text x="1430" y="215" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
    svg_lines.append('      <tspan x="1430" dy="0">inference pods</tspan>')
    svg_lines.append('      <tspan x="1430" dy="30">with readiness,</tspan>')
    svg_lines.append('      <tspan x="1430" dy="30">drain and GPU</tspan>')
    svg_lines.append('      <tspan x="1430" dy="30">health</tspan>')
    svg_lines.append('      <tspan x="1430" dy="30">integration</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')
    
    # ==================== MIDDLE SECTION: TWO PANELS ====================
    # Left Panel: Watch per backend (x=40, y=415, w=740, h=430)
    svg_lines.append('  <!-- Left Panel: Watch per backend -->')
    svg_lines.append('  <g id="panel-metrics">')
    svg_lines.append('    <rect x="40" y="415" width="740" height="430" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon: Dashboard / Graph icon at (65, 427)
    svg_lines.append('    <g transform="translate(65, 427)" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">')
    svg_lines.append('      <rect x="4" y="4" width="38" height="28" rx="4" fill="#ffffff" />')
    svg_lines.append('      <polyline points="10,24 18,14 26,20 34,10" />')
    svg_lines.append('    </g>')
    svg_lines.append('    <text x="125" y="452" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Watch per backend</text>')
    
    # Metrics cards:
    # Row 1: request counts | in-flight requests (y=475, h=52)
    svg_lines.append('    <rect x="65" y="475" width="335" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="232" y="510" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">request counts</text>')
    svg_lines.append('    <rect x="420" y="475" width="335" height="52" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="587" y="510" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">in-flight requests</text>')
    
    # Row 2: queue time | error and retry rates (y=539, h=58)
    svg_lines.append('    <rect x="65" y="539" width="335" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="232" y="576" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">queue time</text>')
    svg_lines.append('    <rect x="420" y="539" width="335" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="587" y="563" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_lines.append('      <tspan x="587" dy="0">error and</tspan>')
    svg_lines.append('      <tspan x="587" dy="26">retry rates</tspan>')
    svg_lines.append('    </text>')
    
    # Row 3: TTFT and ITL percentiles | ejection events (y=609, h=58)
    svg_lines.append('    <rect x="65" y="609" width="335" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="232" y="633" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_lines.append('      <tspan x="232" dy="0">TTFT and ITL</tspan>')
    svg_lines.append('      <tspan x="232" dy="26">percentiles</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('    <rect x="420" y="609" width="335" height="58" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="587" y="646" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">ejection events</text>')
    
    # Row 4: hot-backend alerts (full width, y=679, h=50)
    svg_lines.append('    <rect x="65" y="679" width="690" height="50" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="410" y="713" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">hot-backend alerts</text>')
    
    # Row 5: trace each request across the gateway, the router and the engine (full width, y=741, h=86)
    svg_lines.append('    <rect x="65" y="741" width="690" height="86" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="410" y="774" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_lines.append('      <tspan x="410" dy="0">trace each request across the gateway,</tspan>')
    svg_lines.append('      <tspan x="410" dy="30">the router and the engine</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')
    
    # Right Panel: Streaming hygiene (x=820, y=415, w=740, h=430)
    svg_lines.append('  <!-- Right Panel: Streaming Hygiene -->')
    svg_lines.append('  <g id="panel-streaming">')
    svg_lines.append('    <rect x="820" y="415" width="740" height="430" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Row 1: disable proxy buffering for SSE (y=435, h=54)
    svg_lines.append('    <rect x="845" y="435" width="690" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="1190" y="470" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">disable proxy buffering for SSE</text>')
    
    # Row 2: read and stream-idle timeouts above the maximum generation time (y=501, h=76)
    svg_lines.append('    <rect x="845" y="501" width="690" height="76" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="1190" y="534" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_lines.append('      <tspan x="1190" dy="0">read and stream-idle timeouts</tspan>')
    svg_lines.append('      <tspan x="1190" dy="30">above the maximum generation time</tspan>')
    svg_lines.append('    </text>')
    
    # Row 3: heartbeats (w=240) | avoid Connection: close (w=430) (y=589, h=54)
    svg_lines.append('    <rect x="845" y="589" width="240" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="965" y="624" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">heartbeats</text>')
    svg_lines.append('    <rect x="1105" y="589" width="430" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="1320" y="624" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">avoid Connection: close</text>')
    
    # Row 4: HTTP/2 end to end where possible (y=655, h=54)
    svg_lines.append('    <rect x="845" y="655" width="690" height="54" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="1190" y="690" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">HTTP/2 end to end where possible</text>')
    
    # Row 5: measure time-to-first-token (TTFT) and inter-token latency at the proxy with $upstream_response_time or Envoy stats (y=721, h=106)
    svg_lines.append('    <rect x="845" y="721" width="690" height="106" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg_lines.append('    <text x="1190" y="753" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_lines.append('      <tspan x="1190" dy="0">measure time-to-first-token (TTFT) and</tspan>')
    svg_lines.append('      <tspan x="1190" dy="28">inter-token latency at the proxy with</tspan>')
    svg_lines.append('      <tspan x="1190" dy="28">$upstream_response_time or Envoy stats</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')
    
    # ==================== SECTION 3: SCALING THE L4 TIER STRIP ====================
    # Strip (x=40, y=865, w=1520, h=240)
    svg_lines.append('  <!-- Strip: Scaling the L4 tier -->')
    svg_lines.append('  <g id="strip-l4">')
    svg_lines.append('    <rect x="40" y="865" width="1520" height="240" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg_lines.append('    <text x="800" y="904" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg_lines.append('      <tspan x="800" dy="0">BGP convergence sets how quickly a failed node\'s traffic moves; BFD detects in under a second;</tspan>')
    svg_lines.append('      <tspan x="800" dy="32">resilient or consistent hashing in the router moves only the failed node\'s flows;</tspan>')
    svg_lines.append('      <tspan x="800" dy="32">announce the VIP only while the node can serve; a route change can move a flow to a different site,</tspan>')
    svg_lines.append('      <tspan x="800" dy="32">which breaks long-lived TCP; fabric ECMP caveats: elephant flows,</tspan>')
    svg_lines.append('      <tspan x="800" dy="32">RoCE varies UDP source ports per QP, tunnels need inner-header hashing,</tspan>')
    svg_lines.append('      <tspan x="800" dy="32">adaptive routing reacts to load</tspan>')
    svg_lines.append('    </text>')
    svg_lines.append('  </g>')
    
    # ==================== SECTION 4: BOTTOM BAR ====================
    # Bottom bar (x=40, y=1125, w=1520, h=52)
    svg_lines.append('  <!-- Bottom Bar: Takeaway -->')
    svg_lines.append('  <g id="bottom-bar">')
    svg_lines.append('    <rect x="40" y="1125" width="1520" height="52" rx="10" fill="#207448" />')
    svg_lines.append('    <text x="800" y="1161" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#ffffff">Decide your failover budget first</text>')
    svg_lines.append('  </g>')
    
    svg_lines.append('</svg>')
    
    content = "\n".join(svg_lines)
    with open("inference_path.svg", "w", encoding="utf-8") as f:
        f.write(content)
    print("Generated inference_path.svg successfully!")

generate_svg()
