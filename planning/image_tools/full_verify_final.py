import xml.etree.ElementTree as ET
import re

tree = ET.parse("final.svg")
root = tree.getroot()

def get_text_exact(elem):
    text = elem.text or ""
    for child in elem:
        text += get_text_exact(child)
        if child.tail:
            text += child.tail
    return text

# 1. Check title & desc
title = root.find('{http://www.w3.org/2000/svg}title')
desc = root.find('{http://www.w3.org/2000/svg}desc')
assert title is not None and title.text == "When iptables mode stops scaling", "Title tag mismatch"
assert desc is not None and desc.text == "When iptables mode stops scaling", "Desc tag mismatch"
print("1. Title & Desc: PASSED")

# 2. Check source labels
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
for idx, l in enumerate(source_labels):
    norm_l = " ".join(l.split())
    assert norm_l in all_text, f"Label {idx+1} missing: {norm_l}"
print("2. All 8 source labels found verbatim: PASSED")

# 3. Check zero extra words
root_copy = ET.parse("final.svg").getroot()
root_copy.remove(root_copy.find('{http://www.w3.org/2000/svg}title'))
root_copy.remove(root_copy.find('{http://www.w3.org/2000/svg}desc'))
rem_text = " ".join(get_text_exact(root_copy).split())
for l in source_labels:
    norm_l = " ".join(l.split())
    rem_text = rem_text.replace(norm_l, "", 1)
rem_text = " ".join(rem_text.split())
assert rem_text == "", f"Extra text found: '{rem_text}'"
print("3. Exactly zero extra words: PASSED")

# 4. Check font sizes
with open("final.svg") as f:
    raw_svg = f.read()

font_sizes = [int(x) for x in re.findall(r'font-size="(\d+)"', raw_svg)]
assert min(font_sizes) >= 24, f"Font size < 24 found: {min(font_sizes)}"
assert max(font_sizes) == 48, f"Max font size != 48: {max(font_sizes)}"
print(f"4. Font sizes check (min={min(font_sizes)}px, max={max(font_sizes)}px): PASSED")

# 5. Check colors
colors = set(re.findall(r'#(?:[0-9a-fA-F]{3}){1,2}', raw_svg))
print("Colors present:", colors)
assert "#db8129" in colors, "Orange #db8129 missing"
assert raw_svg.count("#db8129") == 1, f"Orange #db8129 used {raw_svg.count('#db8129')} times (must be exactly 1)!"
print("5. Single orange item check: PASSED (used exactly once on threshold marker)")

# 6. Check dimensions
assert 'viewBox="0 0 1600 1200"' in raw_svg
assert 'width="1600"' in raw_svg
assert 'height="1200"' in raw_svg
print("6. Canvas dimensions (1600x1200): PASSED")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
