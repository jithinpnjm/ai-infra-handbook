import re

def est_width(segments):
    total = 0.0
    for text, fs, is_mono in segments:
        coeff = 0.62 if is_mono else 0.6
        total += len(text) * fs * coeff
    return total

# Let's test the text wrapping for each of the 6 content items.
labels = [
    "The four dnsPolicy values and what they put in resolv.conf",
    "ClusterFirst (the real default): nameserver is the kube-dns ClusterIP; search ns.svc.domain svc.domain domain plus node search domains; options ndots:5; names outside the cluster domain are forwarded upstream by CoreDNS",
    "Default (not the default despite the name): inherit the node resolver config from the node resolv.conf or kubelet resolvConf",
    "ClusterFirstWithHostNet: for hostNetwork true pods that still want cluster DNS; plain ClusterFirst is ignored for hostNetwork pods",
    "None: use only dnsConfig (custom nameservers, searches, options)",
    "options ndots 2, single-request-reopen, timeout 2, attempts 3; searches extra.example.com",
    "job title trap: Default sounds standard but its job is narrower"
]

print("Labels count:", len(labels))
for l in labels:
    print("-", l)
