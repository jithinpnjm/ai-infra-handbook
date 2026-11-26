from test_wrap import est_width

# If icon is beside the title:
# Let card have x_pad = 24, y_pad = 24.
# Icon at (x_pad, y_pad), size 56x56.
# Title starts at x = x_pad + 56 + 16 = x_pad + 72.
# Total card width = 645 (if card itself is 645, or inside container).
# Let's check card widths and line wraps:

# For IPVS:
# Title: "IPVS:" at 30px bold = 5 * 0.6 * 30 = 90px.
# Title fits next to icon: 72 + 90 = 162px < 645!
# Can secondary text start on the same line or line below?
# Prompt: "IPVS: hash lookup O(1), incremental updates, schedulers rr lc sh dh sed nq, needs ip_vs modules and ipset, strictARP true for MetalLB L2"
# If "IPVS: hash lookup O(1)," is on the first line next to the icon:
# 72 + est_width([("IPVS:", 30, False), (" hash lookup O(1),", 24, False)]) = 72 + 349.2 = 421.2 < 645 - 24 = 621!
# Then subsequent lines start at x_pad (full width 645 - 48 = 597px)!
print("IPVS fits!")

# For eBPF:
# Prompt: 'eBPF (Cilium kubeProxyReplacement=true): cgroup/connect4 hook rewrites the destination at connect time, no packet NAT, no conntrack for in-cluster Service traffic, kernel 5.10+ recommended'
# Let's wrap eBPF lines nicely to fit 597px:
ebpf_lines = [
    # Line 1 beside icon (avail 645 - 48 - 72 = 525px):
    [("eBPF", 30, False), (" (Cilium", 24, False)], # 72 + 115.2 = 187.2px < 525!
    # Lines below icon (full width 597px):
    [("kubeProxyReplacement=true):", 24, True)], # 27 * 0.62 * 24 = 401.76 < 597!
    [("cgroup/connect4", 24, True), (" hook rewrites the", 24, False)], # 15*14.88 + 18*14.4 = 223.2 + 259.2 = 482.4 < 597!
    [("destination at connect time, no packet NAT,", 24, False)], # 43 * 14.4 = 619.2 > 597! Let's wrap:
]

# Let's test exact wraps for eBPF
ebpf_wrapped = [
    [("eBPF", 30, False)], # next to icon
    [("(Cilium ", 24, False), ("kubeProxyReplacement=true", 24, True), ("):", 24, False)], # 516px < 597!
    [("cgroup/connect4", 24, True), (" hook rewrites", 24, False)], # 223.2 + 14*14.4 = 424.8 < 597!
    [("the destination at connect time,", 24, False)], # 33 * 14.4 = 475.2 < 597!
    [("no packet NAT, no conntrack for", 24, False)], # 31 * 14.4 = 446.4 < 597!
    [("in-cluster Service traffic,", 24, False)], # 27 * 14.4 = 388.8 < 597!
    [("kernel 5.10+ recommended", 24, False)] # 24 * 14.4 = 345.6 < 597!
]

for i, l in enumerate(ebpf_wrapped):
    w = est_width(l)
    print(f"eBPF line {i+1}: w={w:.1f} / 597 (fits: {w <= 597})")
