import re

def est_width(line_str, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.6
    return len(line_str) * fs * coeff

card1_lines = [
    ("ClusterFirst (the real default):", 30, False),
    ("nameserver is the kube-dns ClusterIP; search", 24, False),
    ("ns.svc.domain svc.domain domain plus node", 24, False),
    ("search domains; options ndots:5; names outside", 24, False),
    ("the cluster domain are forwarded upstream by CoreDNS", 24, False)
]

card2_lines = [
    ("Default (not the default despite the name):", 30, False),
    ("inherit the node resolver config from the", 24, False),
    ("node resolv.conf or kubelet resolvConf", 24, False)
]

card3_lines = [
    ("ClusterFirstWithHostNet:", 30, False),
    ("for hostNetwork true pods that still want", 24, False),
    ("cluster DNS; plain ClusterFirst is ignored for", 24, False),
    ("hostNetwork pods", 24, False)
]

card4_lines = [
    ("None:", 30, False),
    ("use only dnsConfig (custom nameservers,", 24, False),
    ("searches, options)", 24, False)
]

dns_example_lines = [
    ("options ndots 2, single-request-reopen, timeout 2,", 26, False),
    ("attempts 3; searches extra.example.com", 26, False)
]

callout_lines = [
    ("job title trap: Default sounds standard", 26, False),
    ("but its job is narrower", 26, False)
]

all_groups = [
    ("Card 1", card1_lines),
    ("Card 2", card2_lines),
    ("Card 3", card3_lines),
    ("Card 4", card4_lines),
    ("dnsConfig Example", dns_example_lines),
    ("Callout", callout_lines)
]

for name, lines in all_groups:
    print(f"=== {name} ===")
    max_w = 0
    for txt, fs, m in lines:
        w = est_width(txt, fs, m)
        max_w = max(max_w, w)
        print(f"  [{fs}px] {w:5.1f}px : '{txt}'")
    print(f"  Max width: {max_w:.1f}px")
