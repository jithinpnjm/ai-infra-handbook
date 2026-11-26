#!/usr/bin/env python3

def calc_row(t_lines, c_lines):
    # fs = 24
    # pad_top >= 16 -> first baseline = y + 42
    # dy = 28
    # pad_bottom >= 16 -> h = last_baseline + 24
    t_h = 42 + (len(t_lines) - 1) * 28 + 24
    c_h = 42 + (len(c_lines) - 1) * 28 + 24
    h = max(t_h, c_h)
    return h, t_h, c_h

table_rows = [
    (
        "Forged answers, cache poisoning",
        ["Forged answers,", "cache poisoning"],
        "DNSSEC, source-port and query-ID randomisation",
        ["DNSSEC, source-port and", "query-ID randomisation"]
    ),
    (
        "Open resolvers, amplification DDoS",
        ["Open resolvers,", "amplification", "DDoS"],
        "restrict recursion to your own networks, rate-limit responses",
        ["restrict recursion to your own", "networks, rate-limit responses"]
    ),
    (
        "DNS tunnelling exfiltrating data",
        ["DNS tunnelling", "exfiltrating data"],
        "monitor volume, long labels and TXT records",
        ["monitor volume, long labels", "and TXT records"]
    ),
    (
        "Dangling CNAMEs",
        ["Dangling CNAMEs"],
        "subdomain takeover, clean up records",
        ["subdomain takeover,", "clean up records"]
    ),
    (
        "DNS rebinding",
        ["DNS rebinding"],
        "filter private answers",
        ["filter private answers"]
    ),
    (
        "Zone data",
        ["Zone data"],
        "restrict AXFR to secondaries and authenticate with TSIG; keep authoritative and recursive roles on separate servers",
        [
            "restrict AXFR to secondaries and",
            "authenticate with TSIG; keep",
            "authoritative and recursive roles",
            "on separate servers"
        ]
    ),
    (
        "Untrusted network hop",
        ["Untrusted", "network hop"],
        "DoT over TCP/853 and DoH over HTTPS encrypt the stub to resolver hop; mostly unnecessary inside a data centre",
        [
            "DoT over TCP/853 and DoH over",
            "HTTPS encrypt the stub to resolver",
            "hop; mostly unnecessary inside",
            "a data centre"
        ]
    )
]

opt_lines = [
    "RPZ response policy zones or",
    "provider threat-blocking"
]
opt_h = 42 + (len(opt_lines) - 1) * 28 + 24

print("Row heights:")
total_h = 0
for i, (t_lbl, t_l, c_lbl, c_l) in enumerate(table_rows, 1):
    h, th, ch = calc_row(t_l, c_l)
    print(f"Row {i}: h={h} (th={th}, ch={ch}) | T: {len(t_l)} lines, C: {len(c_l)} lines")
    total_h += h

print(f"Optional card h: {opt_h}")
total_h += opt_h
print(f"Total rows height without gaps: {total_h}")
gaps = 7 * 12 # 7 gaps of 12px
print(f"Total with 12px gaps: {total_h + gaps}")
print(f"Table y span: 175 .. {175 + total_h + gaps}")
