# Let's explore alternative layouts for the left side:
# What if:
# Left column of netfilter chains has Docker rules -> Container port 80.
# Right column has ufw / firewalld rule (skipped).
# Where does the orange arrow go?
# "leading to 'container port 80' (orange arrow: 'published port 8080 answers from anywhere')"

# What if container port 80 is to the right of Docker rules, or Docker rules is on the left, container port 80 is on the right, and ufw rule is below or beside?
# Or what if Docker rules is on top-left, ufw rule is on top-right, and container port 80 is to the right or below?

# What if Client -> Host NIC -> netfilter chains is a horizontal chain at the top?
# Let's check:
# Client (left) -> Host NIC (middle) -> netfilter chains (right)?
# But earlier we noted netfilter chains needs width to show the rules.

# What if:
# Client -> Host NIC is vertical or left-to-right:
# What if Client is at x=40..250 (width 210)
# Arrow to Host NIC at x=40..250 (below it) or to the right?
# If Client -> Host NIC is top-to-bottom:
# Client (y=175..265, x=40..300)
# Arrow down to Host NIC (y=305..395, x=40..300)
# Arrow right to netfilter chains (y=175..555, x=340..940, width 600)?
# Let's see: if netfilter chains is width 600, height 380!
# That gives 380px vertical height for netfilter chains!
print("Testing layout with netfilter chains width=600, height=380")
