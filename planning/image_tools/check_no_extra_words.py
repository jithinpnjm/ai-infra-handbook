import xml.etree.ElementTree as ET

tree = ET.parse("test.svg")
root = tree.getroot()

def get_text_exact(elem):
    text = elem.text or ""
    for child in elem:
        text += get_text_exact(child)
        if child.tail:
            text += child.tail
    return text

# Remove title and desc first
title = root.find('{http://www.w3.org/2000/svg}title')
desc = root.find('{http://www.w3.org/2000/svg}desc')
root.remove(title)
root.remove(desc)

raw_text = " ".join(get_text_exact(root).split())
print("Remaining text in SVG after removing <title> and <desc>:")
print(raw_text)

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

remaining = raw_text
for l in source_labels:
    norm_l = " ".join(l.split())
    if norm_l in remaining:
        remaining = remaining.replace(norm_l, "", 1)
    else:
        print(f"Could not remove: {norm_l}")

remaining = " ".join(remaining.split())
print(f"Remaining after removing all source labels: '{remaining}'")
assert remaining == "", f"Extra text found: '{remaining}'"
print("SUCCESS: EXACTLY ZERO EXTRA WORDS OR LABELS IN SVG!")
