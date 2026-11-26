from test_wrap import est_width

footer_lines_2 = [
    [("kubeproxy_sync_proxy_rules_duration_seconds, kubeproxy_sync_proxy_rules_iptables_total,", 24, True)],
    [("kubeproxy_network_programming_duration_seconds", 24, True)]
]
# Wait, order in prompt:
# kubeproxy_sync_proxy_rules_duration_seconds, kubeproxy_network_programming_duration_seconds, kubeproxy_sync_proxy_rules_iptables_total
footer_lines_order = [
    [("kubeproxy_sync_proxy_rules_duration_seconds,", 24, True)],
    [("kubeproxy_network_programming_duration_seconds,", 24, True)],
    [("kubeproxy_sync_proxy_rules_iptables_total", 24, True)]
]
for idx, line in enumerate(footer_lines_order):
    w = est_width(line)
    print(f"3-line footer Line {idx+1}: width={w:.1f}px, text={[t for t,fs,m in line]}")

footer_lines_2_order = [
    [("kubeproxy_sync_proxy_rules_duration_seconds, kubeproxy_network_programming_duration_seconds,", 24, True)],
    [("kubeproxy_sync_proxy_rules_iptables_total", 24, True)]
]
for idx, line in enumerate(footer_lines_2_order):
    w = est_width(line)
    print(f"2-line footer Line {idx+1}: width={w:.1f}px, text={[t for t,fs,m in line]}")

