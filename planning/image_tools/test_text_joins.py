import re

items = [
    # Title
    ("Title", [
        "HTTP/1.1, HTTP/2 and HTTP/3 compared: ",
        "how the request travels"
    ], "HTTP/1.1, HTTP/2 and HTTP/3 compared: how the request travels"),

    # Col 1
    ("C1_title", ["HTTP/1.1"], "HTTP/1.1"),
    ("C1_stack", [
        "HTTP text over TLS ",
        "over TCP"
    ], "HTTP text over TLS over TCP"),
    ("C1_req1", ["GET / HTTP/1.1"], "GET / HTTP/1.1"),
    ("C1_req2", ["Host: example.com"], "Host: example.com"),
    ("C1_req3", ["User-Agent"], "User-Agent"),
    ("C1_req4", ["Accept"], "Accept"),
    ("C1_req5", ["Authorization"], "Authorization"),
    ("C1_resp1", ["HTTP/1.1 200 OK"], "HTTP/1.1 200 OK"),
    ("C1_resp2", [
        "Content-Type, ",
        "Content-Length or ",
        "Transfer-Encoding: chunked, ",
        "caching headers, Set-Cookie"
    ], "Content-Type, Content-Length or Transfer-Encoding: chunked, caching headers, Set-Cookie"),
    ("C1_note", [
        "keep-alive reuses the TCP ",
        "and TLS connection for ",
        "several requests"
    ], "keep-alive reuses the TCP and TLS connection for several requests"),

    # Col 2
    ("C2_title", ["HTTP/2"], "HTTP/2"),
    ("C2_stack", [
        "binary HTTP over TLS ",
        "(ALPN h2) over TCP"
    ], "binary HTTP over TLS (ALPN h2) over TCP"),
    ("C2_note1", ["compresses headers"], "compresses headers"),
    ("C2_note2", [
        "head-of-line blocking now ",
        "happens at the TCP level: ",
        "one stalled TCP packet ",
        "holds up every stream"
    ], "head-of-line blocking now happens at the TCP level: one stalled TCP packet holds up every stream"),

    # Col 3
    ("C3_title", ["HTTP/3"], "HTTP/3"),
    ("C3_stack", [
        "HTTP over QUIC ",
        "(includes TLS 1.3) ",
        "over UDP/443"
    ], "HTTP over QUIC (includes TLS 1.3) over UDP/443"),
    ("C3_note1", [
        "recovers from loss ",
        "per stream"
    ], "recovers from loss per stream"),
    ("C3_note2", ["faster connection setup"], "faster connection setup"),
    ("C3_note3", [
        "supports connection ",
        "migration"
    ], "supports connection migration"),
    ("C3_note4", [
        "try curl --http3 ",
        "if your build supports it"
    ], "try curl --http3 if your build supports it"),

    # Bottom
    ("Bottom_strip", [
        "Redirects 301, 302, 307, 308 trigger a new request, maybe a new connection: curl -L; proxies, CDNs ",
        "and load balancers may terminate TLS, rewrite headers such as X-Forwarded-For, cache and retry"
    ], "Redirects 301, 302, 307, 308 trigger a new request, maybe a new connection: curl -L; proxies, CDNs and load balancers may terminate TLS, rewrite headers such as X-Forwarded-For, cache and retry"),
    ("Timing_strip", [
        "TTFB = time_starttransfer = DNS + connect + TLS + server think time + one RTT; ",
        "time_total adds the body transfer"
    ], "TTFB = time_starttransfer = DNS + connect + TLS + server think time + one RTT; time_total adds the body transfer"),
    ("Bottom_bar", [
        "If headers look right but the page is slow, compare time_starttransfer with time_total"
    ], "If headers look right but the page is slow, compare time_starttransfer with time_total"),
]

print(f"Total items: {len(items)}")
all_match = True
for name, tspans, expected in items:
    joined = re.sub(r'\s+', ' ', "".join(tspans).strip())
    match = (joined == expected)
    if not match:
        all_match = False
        print(f"MISMATCH in {name}:")
        print(f"  Got:      '{joined}'")
        print(f"  Expected: '{expected}'")
    else:
        max_len = max(len(t.strip()) for t in tspans)
        print(f"OK: {name:15} ({len(tspans)} lines, max line {max_len:2d} chars)")

assert all_match
print("All 24 items match expected labels perfectly!")
