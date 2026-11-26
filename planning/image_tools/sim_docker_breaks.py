from sim_layout import check_wrap

def w(s): return len(s) * 24 * 0.6

# Let's test 5 lines:
option1 = [
    "Docker's own NAT and",
    "FORWARD rules (DOCKER",
    "chain) are inserted",
    "ahead of the rules",
    "managed by ufw or firewalld"
]

option2 = [
    "Docker's own NAT and",
    "FORWARD rules (DOCKER chain)",
    "are inserted ahead of the",
    "rules managed by ufw or",
    "firewalld"
]

print("Option 1:")
for l in option1:
    print(f"  {w(l):5.1f}px : {l}")

print("\nOption 2:")
for l in option2:
    print(f"  {w(l):5.1f}px : {l}")
