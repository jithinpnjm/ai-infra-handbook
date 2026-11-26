# Footer (196 chars):
# 'Also: arp_filter=1 answers only if the route to the sender would use this interface; arp_notify sends a gratuitous ARP when an interface comes up or the address changes; all keys are per interface'
footer_text = "Also: arp_filter=1 answers only if the route to the sender would use this interface; arp_notify sends a gratuitous ARP when an interface comes up or the address changes; all keys are per interface"

# Box width = 1520 (x=40..1560)
# Usable width: 1520 - 32 = 1488 px.
# At 24px sans-serif (0.6): max chars = 1488 / (0.6 * 24) = 103 chars per line!

# Let's split Footer into 2 lines:
# 196 / 2 = 98 chars!
# Line 1: "Also: arp_filter=1 answers only if the route to the sender would use this interface;" (84 chars)
# Line 2: "arp_notify sends a gratuitous ARP when an interface comes up or the address changes; all keys are per interface" (111 chars -> 111 * 14.4 = 1598 > 1488!)
# So 3 lines for Footer:
f_lines = [
    "Also: arp_filter=1 answers only if the route to the sender would use this interface;",
    "arp_notify sends a gratuitous ARP when an interface comes up or the address changes;",
    "all keys are per interface"
]
print("Footer lines:")
for l in f_lines:
    w = len(l) * 0.6 * 24
    print(f"  ({len(l):2d} chars, {w:6.1f} px) : {l}")

# Result row (157 chars):
# 'Symptoms without the recipe: asymmetric paths, RDMA and NCCL oddities, flapping MAC tables, confused bonding; often seen only after another NIC is plugged in'
r_lines = [
    "Symptoms without the recipe: asymmetric paths, RDMA and NCCL oddities,",
    "flapping MAC tables, confused bonding; often seen only after another NIC is plugged in"
]
print("\nResult row lines:")
for l in r_lines:
    w = len(l) * 0.6 * 24
    print(f"  ({len(l):2d} chars, {w:6.1f} px) : {l}")

# Bottom bar (106 chars):
# 'Each setting makes the server answer only for the address that belongs to the card the question arrived on'
b_lines = [
    "Each setting makes the server answer only for the address",
    "that belongs to the card the question arrived on"
]
print("\nBottom bar lines:")
for l in b_lines:
    w = len(l) * 0.6 * 24
    print(f"  ({len(l):2d} chars, {w:6.1f} px) : {l}")
