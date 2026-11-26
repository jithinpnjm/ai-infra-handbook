import xml.etree.ElementTree as ET

def get_text_exact(elem):
    text = elem.text or ""
    for child in elem:
        text += get_text_exact(child)
        if child.tail:
            text += child.tail
    return text

with open("test.svg") as f:
    content = f.read()

# Fix KUBE-SERVICES,
content = content.replace(
    '<tspan font-family="monospace">KUBE-SERVICES</tspan>, O(n)',
    '<tspan font-family="monospace">KUBE-SERVICES,</tspan> O(n)'
)
# Fix ipset,
content = content.replace(
    'needs <tspan font-family="monospace">ip_vs</tspan> modules and <tspan font-family="monospace">ipset</tspan>,',
    'needs <tspan font-family="monospace">ip_vs</tspan> modules and <tspan font-family="monospace">ipset,</tspan>'
)
# Fix kubeProxyReplacement=true):
content = content.replace(
    '(Cilium <tspan font-family="monospace">kubeProxyReplacement=true</tspan>):',
    '(Cilium <tspan font-family="monospace">kubeProxyReplacement=true):</tspan>'
)

with open("test.svg", "w") as f:
    f.write(content)

tree = ET.parse("test.svg")
root = tree.getroot()

source_labels = [
    "When iptables mode stops scaling",
    "Per new connection: linear walk of KUBE-SERVICES, O(n)",
    "per change: iptables-restore rewrites the whole ruleset, takes the xtables lock (/run/xtables.lock), seconds or minutes at tens of thousands of rules, can collide with CNI plug-ins and send traffic to stale endpoints",
    "iptables degrades beyond roughly 5,000 Services or 25,000 endpoints",
    "IPVS: hash lookup O(1), incremental updates, schedulers rr lc sh dh sed nq, needs ip_vs modules and ipset, strictARP true for MetalLB L2",
    "nftables: single kube-proxy table with maps, O(1), incremental nft -f deltas",
    "eBPF (Cilium kubeProxyReplacement=true): cgroup/connect4 hook rewrites the destination at connect time, no packet NAT, no conntrack for in-cluster Service traffic, kernel 5.10+ recommended",
    "kubeproxy_sync_proxy_rules_duration_seconds, kubeproxy_network_programming_duration_seconds, kubeproxy_sync_proxy_rules_iptables_total"
]

all_text = " ".join(get_text_exact(root).split())
print("Checking all labels in exact text:")
for i, l in enumerate(source_labels):
    norm_l = " ".join(l.split())
    found = norm_l in all_text
    print(f"Label {i+1}: {'FOUND' if found else 'NOT FOUND'}")
    if not found:
        print(f"  Missing: {norm_l}")

