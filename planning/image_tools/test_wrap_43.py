import textwrap

p1_data = [
    ("flow", "about 5,000 containers connect through one NAT IP to one database IP and port"),
    ("arithmetic", "one source IP has about 60,000 usable ephemeral ports per destination IP and port; each connection to that one database needs its own source port on the gateway"),
    ("failure", "ports run out, new connections get no mapping and time out; the database is healthy, CPU is low, dmesg shows no conntrack drops"),
    ("metaphor", "a car park with a fixed number of spaces: the traffic is not heavy but all the spaces are taken"),
    ("fix", "add NAT gateway IPs and ports (Cloud NAT port allocation), use a pooler such as PgBouncer, shorten TIME_WAIT, reuse connections"),
    ("lesson", "count the tuple dimensions: source IP, destination IP and port")
]

for name, text in p1_data:
    lines = textwrap.wrap(text, width=44)
    print(f"{name} ({len(lines)} lines):")
    for l in lines:
        print(f"  [{len(l)}] {l}")
