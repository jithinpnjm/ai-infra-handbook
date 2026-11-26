# In Lane 2:
# What elements are in Lane 2?
# Title: 'c1 to the Internet' (30px)
# Desc: 'default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge; the outside world only talks to the host'
# Commands:
# 1. 'sysctl -w net.ipv4.ip_forward=1'
# 2. 'iptables -t nat -A POSTROUTING -s 10.10.0.0/24 ! -o br0 -j MASQUERADE'
# 3. 'iptables -I FORWARD -i br0 -j ACCEPT'
# 4. 'iptables -I FORWARD -o br0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT'

# How many total lines if desc is 3 lines and commands are 4 lines?
# Total = 1 (title) + 3 (desc) + 4 (commands) = 8 lines!
# Wait! Can desc be 3 lines?
# Let's test wrapping desc into 3 lines:
d = "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD then POSTROUTING masquerade, leaves through the NIC with the host's address; return traffic is un-NATed by conntrack and delivered back through the bridge; the outside world only talks to the host"
print("Length of d:", len(d)) # 288
# If 3 lines: 288 / 3 = 96 chars per line.
# At 24px sans: 96 * 24 * 0.6 = 1382.4 px.
# Inside a 1520px box, 1520 - 1382.4 = 137.6 px margin!
# Padding on each side = 137.6 / 2 = 68.8 px (well above 16px!).
# So desc fits in THREE lines!
