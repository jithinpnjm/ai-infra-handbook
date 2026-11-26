import re

def est_width(txt, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.6
    return len(txt) * fs * coeff

# Test wrapping for all 4 cards + example + callout with card_width=740, pad=30 -> avail_w = 680

# Card 1:
# ClusterFirst (the real default): nameserver is the kube-dns ClusterIP; search ns.svc.domain svc.domain domain plus node search domains; options ndots:5; names outside the cluster domain are forwarded upstream by CoreDNS
c1 = [
    ("ClusterFirst (the real default):", 30, False),
    ("nameserver is the kube-dns ClusterIP; search", 24, False),
    ("ns.svc.domain svc.domain domain plus node", 24, False),
    ("search domains; options ndots:5; names outside", 24, False),
    ("the cluster domain are forwarded upstream", 24, False),
    ("by CoreDNS", 24, False)
]

# Card 2:
# Default (not the default despite the name): inherit the node resolver config from the node resolv.conf or kubelet resolvConf
c2 = [
    ("Default (not the default", 30, False),
    ("despite the name):", 30, False),
    ("inherit the node resolver config from the", 24, False),
    ("node resolv.conf or kubelet resolvConf", 24, False)
]

# Card 3:
# ClusterFirstWithHostNet: for hostNetwork true pods that still want cluster DNS; plain ClusterFirst is ignored for hostNetwork pods
c3 = [
    ("ClusterFirstWithHostNet:", 30, False),
    ("for hostNetwork true pods that still want", 24, False),
    ("cluster DNS; plain ClusterFirst is ignored", 24, False),
    ("for hostNetwork pods", 24, False)
]

# Card 4:
# None: use only dnsConfig (custom nameservers, searches, options)
c4 = [
    ("None:", 30, False),
    ("use only dnsConfig (custom nameservers,", 24, False),
    ("searches, options)", 24, False)
]

# dnsConfig example:
# options ndots 2, single-request-reopen, timeout 2, attempts 3; searches extra.example.com
c_dns = [
    ("options ndots 2, single-request-reopen,", 26, False),
    ("timeout 2, attempts 3; searches extra.example.com", 26, False)
]

# Callout:
# job title trap: Default sounds standard but its job is narrower
c_callout = [
    ("job title trap: Default sounds standard", 26, False),
    ("but its job is narrower", 26, False)
]

cards = [("Card 1", c1), ("Card 2", c2), ("Card 3", c3), ("Card 4", c4), ("dnsConfig", c_dns), ("Callout", c_callout)]

avail_w = 680
for name, lines in cards:
    print(f"=== {name} (avail_w={avail_w}) ===")
    for txt, fs, m in lines:
        w = est_width(txt, fs, m)
        print(f"  [{fs}px] {w:5.1f}px (rem {avail_w - w:5.1f}px): '{txt}'")
        assert w <= avail_w, f"Overflow in {name}: {txt}"
print("\nALL FIT WITHIN 680px!")
