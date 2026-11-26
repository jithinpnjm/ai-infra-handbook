def get_perfect_svg():
    svg = []
    svg.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
    svg.append('  <title>HTTP/1.1, HTTP/2 and HTTP/3 compared: how the request travels</title>')
    svg.append('  <desc>Three columns comparing HTTP 1.1 over TCP, HTTP 2 multiplexing over TCP with head of line blocking, and HTTP 3 over QUIC on UDP port 443.</desc>')
    
    # Background
    svg.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
    
    # Title (48px bold)
    svg.append('  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">HTTP/1.1, HTTP/2 and HTTP/3 compared: </tspan>')
    svg.append('    <tspan x="800" dy="50">how the request travels</tspan>')
    svg.append('  </text>')

    # =========================================================================
    # COLUMN 1: HTTP/1.1
    # x = 40, y = 145, width = 480, height = 671
    # =========================================================================
    svg.append('  <!-- Column 1: HTTP/1.1 -->')
    svg.append('  <g id="col-http11">')
    svg.append('    <rect x="40" y="145" width="480" height="671" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    
    # Col 1 Icon: text document with lines (56x56)
    svg.append('    <g transform="translate(60, 158)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="4" width="44" height="48" rx="4" />')
    svg.append('      <line x1="16" y1="16" x2="40" y2="16" />')
    svg.append('      <line x1="16" y1="26" x2="40" y2="26" />')
    svg.append('      <line x1="16" y1="36" x2="32" y2="36" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="198" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">HTTP/1.1</text>')
    
    # Col 1 Stack Card (h = 82, y = 216 to 298)
    svg.append('    <g id="c1-stack">')
    svg.append('      <rect x="60" y="216" width="440" height="82" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="280" y="251" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="280" dy="0">HTTP text over TLS </tspan>')
    svg.append('        <tspan x="280" dy="28">over TCP</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Col 1 Request Card (drawn as lines, h = 186, y = 306 to 492)
    svg.append('    <g id="c1-request">')
    svg.append('      <rect x="60" y="306" width="440" height="186" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="85" y="342" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">GET / HTTP/1.1</text>')
    svg.append('      <text x="85" y="372" font-family="monospace" font-size="24" fill="#303a36">Host: example.com</text>')
    svg.append('      <text x="85" y="402" font-family="monospace" font-size="24" fill="#303a36">User-Agent</text>')
    svg.append('      <text x="85" y="432" font-family="monospace" font-size="24" fill="#303a36">Accept</text>')
    svg.append('      <text x="85" y="462" font-family="monospace" font-size="24" fill="#303a36">Authorization</text>')
    svg.append('    </g>')

    # Col 1 Response Card (h = 192, y = 500 to 692)
    svg.append('    <g id="c1-response">')
    svg.append('      <rect x="60" y="500" width="440" height="192" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="85" y="538" font-family="monospace" font-size="24" font-weight="bold" fill="#207448">HTTP/1.1 200 OK</text>')
    svg.append('      <text x="85" y="568" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="85" dy="0">Content-Type, </tspan>')
    svg.append('        <tspan x="85" dy="28">Content-Length or </tspan>')
    svg.append('        <tspan x="85" dy="28">Transfer-Encoding: chunked, </tspan>')
    svg.append('        <tspan x="85" dy="28">caching headers, Set-Cookie</tspan>')
    svg.append('      </text>')
    # Visual blank line and body representation
    svg.append('      <rect x="85" y="664" width="390" height="18" rx="4" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 2" />')
    svg.append('    </g>')

    # Col 1 Note Card (keep-alive, h = 114, y = 698 to 812)
    svg.append('    <g id="c1-note">')
    svg.append('      <rect x="60" y="698" width="440" height="114" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="280" y="738" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="280" dy="0">keep-alive reuses the TCP </tspan>')
    svg.append('        <tspan x="280" dy="28">and TLS connection for </tspan>')
    svg.append('        <tspan x="280" dy="28">several requests</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('  </g>')

    # =========================================================================
    # COLUMN 2: HTTP/2
    # x = 560, y = 145, width = 480, height = 671
    # =========================================================================
    svg.append('  <!-- Column 2: HTTP/2 -->')
    svg.append('  <g id="col-http2">')
    svg.append('    <rect x="560" y="145" width="480" height="671" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    
    # Col 2 Icon: parallel multiplexed channels (56x56)
    svg.append('    <g transform="translate(580, 158)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="6" width="44" height="44" rx="6" />')
    svg.append('      <line x1="16" y1="6" x2="16" y2="50" />')
    svg.append('      <line x1="28" y1="6" x2="28" y2="50" />')
    svg.append('      <line x1="40" y1="6" x2="40" y2="50" />')
    svg.append('    </g>')
    svg.append('    <text x="655" y="198" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">HTTP/2</text>')

    # Col 2 Stack Card (h = 82, y = 216 to 298)
    svg.append('    <g id="c2-stack">')
    svg.append('      <rect x="580" y="216" width="440" height="82" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="800" y="251" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="800" dy="0">binary HTTP over TLS </tspan>')
    svg.append('        <tspan x="800" dy="28">(ALPN h2) over TCP</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Col 2 Picture of many streams multiplexed on one connection (h = 216, y = 306 to 522)
    svg.append('    <g id="c2-streams-pic">')
    svg.append('      <rect x="580" y="306" width="440" height="216" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    # Outer TCP connection pipe
    svg.append('      <rect x="600" y="318" width="400" height="190" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="2" />')
    # Four interleaved multiplexed streams inside one connection pipe
    # Stream 1 frames (Dark green)
    svg.append('      <rect x="615" y="331" width="85" height="34" rx="4" fill="#207448" opacity="0.85" />')
    svg.append('      <rect x="715" y="331" width="115" height="34" rx="4" fill="#207448" opacity="0.85" />')
    svg.append('      <rect x="845" y="331" width="140" height="34" rx="4" fill="#207448" opacity="0.85" />')
    # Stream 3 frames (Medium green)
    svg.append('      <rect x="615" y="375" width="130" height="34" rx="4" fill="#2e8b57" opacity="0.8" />')
    svg.append('      <rect x="760" y="375" width="105" height="34" rx="4" fill="#2e8b57" opacity="0.8" />')
    svg.append('      <rect x="880" y="375" width="105" height="34" rx="4" fill="#2e8b57" opacity="0.8" />')
    # Stream 5 frames (Forest green)
    svg.append('      <rect x="615" y="419" width="100" height="34" rx="4" fill="#1b4d3e" opacity="0.8" />')
    svg.append('      <rect x="730" y="419" width="135" height="34" rx="4" fill="#1b4d3e" opacity="0.8" />')
    svg.append('      <rect x="880" y="419" width="105" height="34" rx="4" fill="#1b4d3e" opacity="0.8" />')
    # Stream 7 frames (Mint green with border)
    svg.append('      <rect x="615" y="463" width="115" height="34" rx="4" fill="#3cb371" opacity="0.8" />')
    svg.append('      <rect x="745" y="463" width="110" height="34" rx="4" fill="#3cb371" opacity="0.8" />')
    svg.append('      <rect x="870" y="463" width="115" height="34" rx="4" fill="#3cb371" opacity="0.8" />')
    svg.append('    </g>')

    # Col 2 Note 1: compresses headers (h = 66, y = 530 to 596)
    svg.append('    <g id="c2-note1">')
    svg.append('      <rect x="580" y="530" width="440" height="66" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="800" y="571" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">compresses headers</text>')
    svg.append('    </g>')

    # Col 2 Note 2 (ORANGE): head-of-line blocking now happens at the TCP level... (h = 206, y = 604 to 810)
    svg.append('    <g id="c2-note2-orange">')
    svg.append('      <rect x="580" y="604" width="440" height="206" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    svg.append('      <text x="800" y="647" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="800" dy="0">head-of-line blocking now </tspan>')
    svg.append('        <tspan x="800" dy="36">happens at the TCP level: </tspan>')
    svg.append('        <tspan x="800" dy="36">one stalled TCP packet </tspan>')
    svg.append('        <tspan x="800" dy="36">holds up every stream</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('  </g>')

    # =========================================================================
    # COLUMN 3: HTTP/3
    # x = 1080, y = 145, width = 480, height = 671
    # =========================================================================
    svg.append('  <!-- Column 3: HTTP/3 -->')
    svg.append('  <g id="col-http3">')
    svg.append('    <rect x="1080" y="145" width="480" height="671" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    
    # Col 3 Icon: UDP datagram lightning (56x56)
    svg.append('    <g transform="translate(1100, 158)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 4 L 12 28 L 26 28 L 22 50 L 44 22 L 30 22 Z" />')
    svg.append('    </g>')
    svg.append('    <text x="1175" y="198" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">HTTP/3</text>')

    # Col 3 Stack Card (h = 114, y = 216 to 330)
    svg.append('    <g id="c3-stack">')
    svg.append('      <rect x="1100" y="216" width="440" height="114" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="1320" y="254" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="1320" dy="0">HTTP over QUIC </tspan>')
    svg.append('        <tspan x="1320" dy="28">(includes TLS 1.3) </tspan>')
    svg.append('        <tspan x="1320" dy="28">over UDP/443</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Col 3 Note 1: recovers from loss per stream (h = 88, y = 338 to 426)
    svg.append('    <g id="c3-note1">')
    svg.append('      <rect x="1100" y="338" width="440" height="88" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="1320" y="375" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="1320" dy="0">recovers from loss </tspan>')
    svg.append('        <tspan x="1320" dy="28">per stream</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Col 3 Note 2: faster connection setup (h = 66, y = 434 to 500)
    svg.append('    <g id="c3-note2">')
    svg.append('      <rect x="1100" y="434" width="440" height="66" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="1320" y="475" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">faster connection setup</text>')
    svg.append('    </g>')

    # Col 3 Note 3: supports connection migration (h = 88, y = 508 to 596)
    svg.append('    <g id="c3-note3">')
    svg.append('      <rect x="1100" y="508" width="440" height="88" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="1320" y="545" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('        <tspan x="1320" dy="0">supports connection </tspan>')
    svg.append('        <tspan x="1320" dy="28">migration</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')

    # Col 3 Note 4: try curl --http3 if your build supports it (h = 92, y = 604 to 696)
    svg.append('    <g id="c3-note4">')
    svg.append('      <rect x="1100" y="604" width="440" height="92" rx="8" fill="#ffffff" stroke="#207448" stroke-width="2" />')
    svg.append('      <text x="1320" y="642" text-anchor="middle" font-family="monospace" font-size="24" fill="#207448">')
    svg.append('        <tspan x="1320" dy="0">try curl --http3 </tspan>')
    svg.append('        <tspan x="1320" dy="28" font-family="sans-serif" fill="#303a36">if your build supports it</tspan>')
    svg.append('      </text>')
    svg.append('    </g>')
    svg.append('  </g>')

    # =========================================================================
    # BOTTOM PANELS
    # =========================================================================
    # Bottom strip: Redirects... (h = 96, y = 856 to 952)
    svg.append('  <!-- Bottom Strip: Redirects -->')
    svg.append('  <g id="strip-redirects">')
    svg.append('    <rect x="40" y="856" width="1520" height="96" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="60" y="896" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="60" dy="0">Redirects 301, 302, 307, 308 trigger a new request, maybe a new connection: curl -L; proxies, CDNs </tspan>')
    svg.append('      <tspan x="60" dy="32">and load balancers may terminate TLS, rewrite headers such as X-Forwarded-For, cache and retry</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Timing strip: TTFB... (h = 68, y = 992 to 1060)
    svg.append('  <!-- Timing Strip -->')
    svg.append('  <g id="strip-timing">')
    svg.append('    <rect x="40" y="992" width="1520" height="68" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="800" y="1035" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">TTFB = time_starttransfer = DNS + connect + TLS + server think time + one RTT; time_total adds the body transfer</text>')
    svg.append('  </g>')

    # Bottom bar (Takeaway): If headers look right... (h = 60, y = 1100 to 1160)
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <g id="bar-takeaway">')
    svg.append('    <rect x="40" y="1100" width="1520" height="60" rx="8" fill="#207448" />')
    svg.append('    <text x="800" y="1138" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">If headers look right but the page is slow, compare time_starttransfer with time_total</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

svg_str = get_perfect_svg()
with open("test_candidate.svg", "w") as f:
    f.write(svg_str)

import test_pad_helper
ok = test_pad_helper.test_svg_content(svg_str)
print(f"Overall padding result: {'SUCCESS' if ok else 'FAIL'}")
