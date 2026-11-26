import re

# Font width estimation rules from prompt:
# sans: 0.6 * font_size * char_count
# monospace: 0.62 * font_size * char_count

def est_width(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    return len(text) * fs * factor

labels_to_check = [
    # Title
    ("How parallel A and AAAA queries race", 48, False),
    ("in conntrack and cause a 5-second stall", 48, False),
    # Pod & resolver
    ("pod", 30, False),
    ("glibc resolver", 26, False),
    ("one UDP socket", 24, True),
    ("both to the same source IP and port", 24, False),
    ("A query", 24, False),
    ("AAAA query", 24, False),
    # Step 1
    ("netfilter", 30, False),
    ("conntrack", 26, True),
    ("two side-by-side insertion slots", 24, False),
    # Step 2
    ("kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC", 24, False),
    ("the two packets may go to different CoreDNS pods", 24, False),
    # Step 3
    ("the second insertion collides with the first", 24, False),
    ("insert_failed", 24, True),
    ("the packet is silently dropped", 24, False),
    # Step 4
    ("waits for default 5 s timeout, then retries", 24, False),
    # Fix path
    ("NodeLocal DNSCache removes the DNAT with a NOTRACK note", 24, False),
    ("single-request-reopen separates the two queries", 24, False),
    ("TCP to DNS avoids the UDP path", 24, False),
    # Takeaway
    ("two parallel queries on one socket can collide in the kernel, and the lost packet costs a timeout.", 25, False),
]

for text, fs, mono in labels_to_check:
    w = est_width(text, fs, mono)
    print(f"[{fs}px {'mono' if mono else 'sans'}] len={len(text):2d} w={w:5.1f}px : '{text}'")
