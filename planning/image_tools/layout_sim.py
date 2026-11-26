import re

spec_labels = [
    'HTTP/1.1, HTTP/2 and HTTP/3 compared: how the request travels',
    'HTTP/1.1',
    'HTTP text over TLS over TCP',
    'GET / HTTP/1.1',
    'Host: example.com',
    'User-Agent',
    'Accept',
    'Authorization',
    'HTTP/1.1 200 OK',
    'Content-Type, Content-Length or Transfer-Encoding: chunked, caching headers, Set-Cookie',
    'keep-alive reuses the TCP and TLS connection for several requests',
    'HTTP/2',
    'binary HTTP over TLS (ALPN h2) over TCP',
    'compresses headers',
    'head-of-line blocking now happens at the TCP level: one stalled TCP packet holds up every stream',
    'HTTP/3',
    'HTTP over QUIC (includes TLS 1.3) over UDP/443',
    'recovers from loss per stream',
    'faster connection setup',
    'supports connection migration',
    'try curl --http3 if your build supports it',
    'Redirects 301, 302, 307, 308 trigger a new request, maybe a new connection: curl -L; proxies, CDNs and load balancers may terminate TLS, rewrite headers such as X-Forwarded-For, cache and retry',
    'TTFB = time_starttransfer = DNS + connect + TLS + server think time + one RTT; time_total adds the body transfer',
    'If headers look right but the page is slow, compare time_starttransfer with time_total'
]

print(f"Total labels: {len(spec_labels)}")
for i, l in enumerate(spec_labels, 1):
    print(f"[{i:2d}] {len(l)} chars: {l}")
