import re

# Prompt content string:
# "How parallel A and AAAA queries race in conntrack and cause a 5-second stall"
# Labels to check:
labels = [
    "How parallel A and AAAA queries race in conntrack and cause a 5-second stall",
    "pod",
    "glibc resolver",
    "one UDP socket",
    "A query",
    "AAAA query",
    "both to the same source IP and port",
    "netfilter",
    "conntrack",
    "two side-by-side insertion slots",
    "kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC",
    "the two packets may go to different CoreDNS pods",
    "the second insertion collides with the first",
    "insert_failed",
    "the packet is silently dropped",
    "waits for default 5 s timeout, then retries",
    "NodeLocal DNSCache removes the DNAT with a NOTRACK note",
    "single-request-reopen separates the two queries",
    "TCP to DNS avoids the UDP path",
    "two parallel queries on one socket can collide in the kernel, and the lost packet costs a timeout"
]

print("Total labels to verify:", len(labels))
for idx, l in enumerate(labels, 1):
    print(f"{idx:2d}. {l}")
