# Let's test if two columns in Lane 1 and Lane 2 work cleanly!

# In Lane 1:
# Width = 1520.
# Left side: Desc (width 850)
# Right side: Note (width 600)
# Gap between left and right = 70.
# Left usable width = 850 - 32 = 818 -> 818 / (24*0.6) = 56 chars.
# Right usable width = 600 - 32 = 568 -> 568 / (24*0.6) = 39 chars.

def wrap(text, max_chars):
    words = text.split(' ')
    lines = []
    cur = []
    cur_len = 0
    for w in words:
        if cur_len + len(w) + (1 if cur else 0) <= max_chars:
            cur.append(w)
            cur_len += len(w) + (1 if len(cur) > 1 else 0)
        else:
            lines.append(' '.join(cur))
            cur = [w]
            cur_len = len(w)
    if cur:
        lines.append(' '.join(cur))
    return lines

desc = "c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame to c2's veth and eth0"
note = "br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic; Kubernetes requires it so kube-proxy rules apply"

print("Desc in 56 chars:")
d_lines = wrap(desc, 56)
for l in d_lines:
    print(f"  ({len(l)}) {l}")

print("\nNote in 39 chars:")
n_lines = wrap(note, 39)
for l in n_lines:
    print(f"  ({len(l)}) {l}")

