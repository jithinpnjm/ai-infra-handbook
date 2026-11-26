import textwrap

items_p1 = [
    ("flow", "about 5,000 containers connect through one NAT IP to one database IP and port"),
    ("arithmetic", "one source IP has about 60,000 usable ephemeral ports per destination IP and port; each connection to that one database needs its own source port on the gateway"),
    ("failure", "ports run out, new connections get no mapping and time out; the database is healthy, CPU is low, dmesg shows no conntrack drops"),
    ("metaphor", "a car park with a fixed number of spaces: the traffic is not heavy but all the spaces are taken"),
    ("fix", "add NAT gateway IPs and ports (Cloud NAT port allocation), use a pooler such as PgBouncer, shorten TIME_WAIT, reuse connections"),
    ("lesson", "count the tuple dimensions: source IP, destination IP and port")
]

items_p2 = [
    ("symptom", "busy Kubernetes nodes, intermittent timeouts for new connections, CPU and bandwidth fine"),
    ("evidence", "dmesg: nf_conntrack: table full, dropping packet; conntrack -C equals nf_conntrack_max; conntrack -S shows insert_failed"),
    ("causes", "established timeout of 5 days keeps dead flows forever; table too small for the load"),
    ("note", "established connections keep working, only new ones fail"),
    ("fix", "raise the max and hash size, lower timeouts, find chatty clients, notrack for DNS and east-west flows")
]

# Let's see: if each card has text width of ~580 px (about 39 chars per line)
for name, text in items_p1:
    lines = textwrap.wrap(text, width=38)
    print(f"P1 {name} ({len(lines)} lines):")
    for l in lines:
        print(f"  {l}")

print("\n--- P2 ---")
for name, text in items_p2:
    lines = textwrap.wrap(text, width=38)
    print(f"P2 {name} ({len(lines)} lines):")
    for l in lines:
        print(f"  {l}")
