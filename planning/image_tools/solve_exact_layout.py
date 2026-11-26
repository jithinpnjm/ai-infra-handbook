# Let's write an exact layout solver where:
# - Canvas is 1600 x 1200
# - Margins are 40px (left=40, right=40, top=40, bottom=40)
# - Gap between all standalone boxes >= 40px
# - Every text line has >= 16px padding inside its box
# - Font sizes: Title 48px, Section titles >= 30px, secondary/monospace >= 24px

# Let's inspect the boxes:
# What if the 4 shared nodes are at the top of the lanes or part of Host?
# Wait! Does the prompt require Shared Nodes to be a separate box with 40px gap?
# Prompt:
# "Three horizontal lanes sharing a host with bridge br0 (10.10.0.1/24), containers c1 (10.10.0.11) and c2 (10.10.0.12), and an uplink NIC."
# "Lane 1 'c1 to c2 on the same bridge': ..."
# "Lane 2 'c1 to the Internet': ..."
# "Lane 3 'host:8080 to c1:80' (orange): ..."
# "Footer 'DNS inside: mkdir /etc/netns/c1 and write nameserver 1.1.1.1 to /etc/netns/c1/resolv.conf'."
# "Docker note 'almost literally what the default bridge network does: docker0, a veth per container, an IPAM address from a private pool, a default route via the bridge, masquerade, DNAT for published ports, a bind-mounted /etc/resolv.conf'."
# "Bottom bar: 'A container is only a namespace plus a cable'."

# Notice that the prompt says:
# "Three horizontal lanes sharing a host with bridge br0 (10.10.0.1/24), containers c1 (10.10.0.11) and c2 (10.10.0.12), and an uplink NIC."
# What if the Host is an outer container (subgraph):
# Subgraph = Host!
# Inside the Host container:
# There are 3 horizontal lanes!
# And what about br0 (10.10.0.1/24), c1 (10.10.0.11), c2 (10.10.0.12), uplink NIC?
# They are the shared components of the Host!
# They can be displayed at the top of the Host container!

# Let's see: How many outer boxes are there on the canvas?
# Outer Box 1: Host container (containing shared components + Lane 1 + Lane 2 + Lane 3)
# Outer Box 2: Footer & Docker note box
# Outer Box 3: Bottom takeaway bar

# Between Outer Box 1 and Outer Box 2: gap >= 40px!
# Between Outer Box 2 and Outer Box 3: gap >= 40px!
# Title to Outer Box 1: gap >= 40px!
# Bottom margin: >= 40px!
print("Let's test this structure!")
