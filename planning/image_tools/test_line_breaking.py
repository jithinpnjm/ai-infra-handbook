import textwrap

# Exact labels:
p1_labels = [
    ("flow", "about 5,000 containers connect through one NAT IP to one database IP and port", "sans"),
    ("arithmetic", "one source IP has about 60,000 usable ephemeral ports per destination IP and port; each connection to that one database needs its own source port on the gateway", "sans"),
    ("failure", "ports run out, new connections get no mapping and time out; the database is healthy, CPU is low, dmesg shows no conntrack drops", "sans"),
    ("metaphor", "a car park with a fixed number of spaces: the traffic is not heavy but all the spaces are taken", "sans"),
    ("fix", "add NAT gateway IPs and ports (Cloud NAT port allocation), use a pooler such as PgBouncer, shorten TIME_WAIT, reuse connections", "sans"),
    ("lesson", "count the tuple dimensions: source IP, destination IP and port", "sans")
]

p2_labels = [
    ("symptom", "busy Kubernetes nodes, intermittent timeouts for new connections, CPU and bandwidth fine", "sans"),
    ("evidence", "dmesg: nf_conntrack: table full, dropping packet; conntrack -C equals nf_conntrack_max; conntrack -S shows insert_failed", "mono"),
    ("causes", "established timeout of 5 days keeps dead flows forever; table too small for the load", "sans"),
    ("note", "established connections keep working, only new ones fail", "sans"),
    ("fix", "raise the max and hash size, lower timeouts, find chatty clients, notrack for DNS and east-west flows", "sans")
]

max_w = 560 # Available text width

print("=== Panel 1 Lines ===")
for name, text, font_type in p1_labels:
    w_chars = 37 if font_type == "mono" else 38
    lines = textwrap.wrap(text, width=w_chars)
    char_w = 14.88 if font_type == "mono" else 14.4
    print(f"\n{name} ({len(lines)} lines):")
    for l in lines:
        px_w = len(l) * char_w
        assert px_w <= max_w, f"Line too long: {l} ({px_w}px > {max_w}px)"
        print(f"  [{len(l):2d} ch | {px_w:5.1f}px] {l}")

print("\n=== Panel 2 Lines ===")
for name, text, font_type in p2_labels:
    w_chars = 37 if font_type == "mono" else 38
    lines = textwrap.wrap(text, width=w_chars)
    char_w = 14.88 if font_type == "mono" else 14.4
    print(f"\n{name} ({len(lines)} lines):")
    for l in lines:
        px_w = len(l) * char_w
        assert px_w <= max_w, f"Line too long: {l} ({px_w}px > {max_w}px)"
        print(f"  [{len(l):2d} ch | {px_w:5.1f}px] {l}")

print("\nALL LINES FIT SAFELY!")
