import re

# Let's define the exact lines for each label:
label_lines = {
    "title": [
        "Two state-table limits that look like",
        "random timeouts: SNAT ports and conntrack"
    ],
    "p1_header": [
        "Case 1: SNAT port exhaustion"
    ],
    "p1_flow": [
        "about 5,000 containers connect through",
        "one NAT IP to one database IP and port"
    ],
    "p1_arith": [
        "one source IP has about 60,000 usable",
        "ephemeral ports per destination IP and",
        "port; each connection to that one",
        "database needs its own source port on",
        "the gateway"
    ],
    "p1_fail": [
        "ports run out, new connections get no",
        "mapping and time out; the database is",
        "healthy, CPU is low, dmesg shows no",
        "conntrack drops"
    ],
    "p1_metaphor": [
        "a car park with a fixed number of",
        "spaces: the traffic is not heavy but",
        "all the spaces are taken"
    ],
    "p1_fix": [
        "add NAT gateway IPs and ports (Cloud",
        "NAT port allocation), use a pooler",
        "such as PgBouncer, shorten TIME_WAIT,",
        "reuse connections"
    ],
    "p1_lesson": [
        "count the tuple dimensions: source IP,",
        "destination IP and port"
    ],
    "p2_header": [
        "Case 3: Conntrack table full"
    ],
    "p2_symptom": [
        "busy Kubernetes nodes, intermittent",
        "timeouts for new connections, CPU and",
        "bandwidth fine"
    ],
    "p2_evidence": [
        "dmesg: nf_conntrack: table full,",
        "dropping packet; conntrack -C equals",
        "nf_conntrack_max; conntrack -S shows",
        "insert_failed"
    ],
    "p2_causes": [
        "established timeout of 5 days keeps",
        "dead flows forever; table too small",
        "for the load"
    ],
    "p2_note": [
        "established connections keep working,",
        "only new ones fail"
    ],
    "p2_fix": [
        "raise the max and hash size, lower",
        "timeouts, find chatty clients, notrack",
        "for DNS and east-west flows"
    ],
    "bottom_bar": [
        "Capacity limits in state tables look like random packet loss"
    ]
}

# Verify that joining each list with a space recreates the exact source string!
original_labels = {
    "title": "Two state-table limits that look like random timeouts: SNAT ports and conntrack",
    "p1_header": "Case 1: SNAT port exhaustion",
    "p1_flow": "about 5,000 containers connect through one NAT IP to one database IP and port",
    "p1_arith": "one source IP has about 60,000 usable ephemeral ports per destination IP and port; each connection to that one database needs its own source port on the gateway",
    "p1_fail": "ports run out, new connections get no mapping and time out; the database is healthy, CPU is low, dmesg shows no conntrack drops",
    "p1_metaphor": "a car park with a fixed number of spaces: the traffic is not heavy but all the spaces are taken",
    "p1_fix": "add NAT gateway IPs and ports (Cloud NAT port allocation), use a pooler such as PgBouncer, shorten TIME_WAIT, reuse connections",
    "p1_lesson": "count the tuple dimensions: source IP, destination IP and port",
    "p2_header": "Case 3: Conntrack table full",
    "p2_symptom": "busy Kubernetes nodes, intermittent timeouts for new connections, CPU and bandwidth fine",
    "p2_evidence": "dmesg: nf_conntrack: table full, dropping packet; conntrack -C equals nf_conntrack_max; conntrack -S shows insert_failed",
    "p2_causes": "established timeout of 5 days keeps dead flows forever; table too small for the load",
    "p2_note": "established connections keep working, only new ones fail",
    "p2_fix": "raise the max and hash size, lower timeouts, find chatty clients, notrack for DNS and east-west flows",
    "bottom_bar": "Capacity limits in state tables look like random packet loss"
}

for k, orig in original_labels.items():
    joined = " ".join(label_lines[k])
    assert joined == orig, f"Mismatch in {k}!\nOriginal: {orig}\nJoined:   {joined}"
    print(f"Verified {k}: OK!")

