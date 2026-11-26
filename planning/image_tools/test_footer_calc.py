from test_wrap import est_width

f_lines = [
    [("kubeproxy_sync_proxy_rules_duration_seconds,", 24, True)],
    [("kubeproxy_network_programming_duration_seconds,", 24, True)],
    [("kubeproxy_sync_proxy_rules_iptables_total", 24, True)]
]

for i, l in enumerate(f_lines):
    w = est_width(l)
    print(f"Footer Line {i+1}: w={w:.1f}px")

