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

# Canvas width = 1600.
# Box width = 1520 (margins 40 left and right).
# Inside box: padding 20 left and right -> 1480 usable width.
# At font-size 24px:
# Sans: 0.6 * 24 = 14.4 px per char -> 1480 / 14.4 = 102 chars!
# Monospace: 0.62 * 24 = 14.88 px per char -> 1480 / 14.88 = 99 chars!

# What if each lane has:
# Left column: lane header, number badge, icon, and path diagram/arrow (e.g. width 400 or 500)
# Right column: description, commands, notes (width 1000 or 950)?
# OR full width with header row, then content?
# Let's see:
# If full width:
# In Lane 1:
# - Title row: Number circle 1, icon, 'c1 to c2 on the same bridge' (30px) + arrow visual
# - Desc:
#   c1's own stack routes the packet because both share a subnet, ARP finds c2, the packet leaves c1's eth0 (veth peer), enters the host-side veth, the bridge learns the MAC and forwards the frame to c2's veth and eth0
#   (len 217 chars -> at 95 chars/line, 3 lines)
# - Note:
#   br_netfilter and net.bridge.bridge-nf-call-iptables=1 let iptables see bridged traffic; Kubernetes requires it so kube-proxy rules apply
#   (len 140 chars -> at 95 chars/line, 2 lines)
# Total lines in Lane 1: Title (36px) + 3 lines (3*30=90px) + 2 lines note (2*30=60px) + paddings (~50px) = ~236px!

# In Lane 2:
# - Title row: Number circle 2, icon, 'c1 to the Internet' (30px) + arrow visual
# - Desc:
#   default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge; the outside world only talks to the host
#   (len 288 chars -> at 95 chars/line, 3-4 lines)
# - Commands (4 lines of mono):
#   sysctl -w net.ipv4.ip_forward=1
#   iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE
#   iptables -I FORWARD -i br0 -j ACCEPT
#   iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
# Total lines in Lane 2: Title + 4 lines desc (120px) + 4 commands (120px) + paddings = ~320px!

# In Lane 3:
# - Title row: Number circle 3, icon, 'host:8080 to c1:80' (30px) + arrow visual
# - Commands (2 lines of mono):
#   iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 10.10.0.11:80 (88 chars)
#   iptables -t nat -A OUTPUT -p tcp -d 127.0.0.1 --dport 8080 -j DNAT ... for local clients (88 chars)
# Total in Lane 3: Title + 2 commands = ~140px!

# Footer & Docker note:
# Can be side-by-side or stacked!
# If side-by-side:
# Left (width 740): DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf (2 lines)
# Right (width 740): Docker note: almost literally what... (4 lines)
# Height = ~130px!

# Bottom bar:
# 'A container is only a namespace plus a cable'
# Height = ~50px!

print("Lane 1:", 220)
print("Lane 2:", 300)
print("Lane 3:", 140)
print("Footer:", 130)
print("Bottom bar:", 50)
print("Total lanes + footer + bar =", 220 + 300 + 140 + 130 + 50)
