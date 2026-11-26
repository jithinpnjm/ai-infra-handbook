# Let us check exact text wrapping and width calculations for each element.

def est_w(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * factor * fs

# 1. Title
t = "Reading hosts.ini: hosts, groups, groups of groups"
print(f"Title width: {est_w(t, 48):.1f} px (avail: 1520 px)")

# 2. File line 1: '[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12'
l1_tspans = [
    "[gpu]",
    "gpu01 ansible_host=10.0.10.11,",
    "gpu02 ansible_host=10.0.10.12"
]
for tsp in l1_tspans:
    print(f"L1 '{tsp}': {est_w(tsp, 24, True):.1f} px")

# 3. File line 2: '[login] login01 ansible_host=10.0.10.5'
l2_tspans = [
    "[login]",
    "login01 ansible_host=10.0.10.5"
]
for tsp in l2_tspans:
    print(f"L2 '{tsp}': {est_w(tsp, 24, True):.1f} px")

# 4. File line 3: '[cluster:children] gpu login'
l3_tspans = [
    "[cluster:children]",
    "gpu login"
]
for tsp in l3_tspans:
    print(f"L3 '{tsp}': {est_w(tsp, 24, True):.1f} px")

# 5. File line 4: '[cluster:vars] ansible_user=automation, ansible_python_interpreter=/usr/bin/python3'
l4_tspans = [
    "[cluster:vars]",
    "ansible_user=automation,",
    "ansible_python_interpreter=/usr/bin/python3"
]
for tsp in l4_tspans:
    print(f"L4 '{tsp}': {est_w(tsp, 24, True):.1f} px")

# 6. Callout 1: 'each host has a name and optionally an address'
c1_tspans = [
    "each host has a name and",
    "optionally an address"
]
for tsp in c1_tspans:
    print(f"C1 '{tsp}': {est_w(tsp, 24, False):.1f} px")

# 7. Callout 2: 'a group collects hosts that share a role'
c2_tspans = [
    "a group collects hosts that",
    "share a role"
]
for tsp in c2_tspans:
    print(f"C2 '{tsp}': {est_w(tsp, 24, False):.1f} px")

# 8. Callout 3 (orange):
c3_tspans = [
    "a group of groups, written with :children, lets one command reach every",
    "member: a play aimed at cluster reaches all three machines"
]
for tsp in c3_tspans:
    print(f"C3 '{tsp}': {est_w(tsp, 24, False):.1f} px")

# 9. Vars box: 'ansible_user and interpreter apply to all three machines'
vb_tspans = [
    "ansible_user and interpreter",
    "apply to all three machines"
]
for tsp in vb_tspans:
    print(f"VB '{tsp}': {est_w(tsp, 24, False):.1f} px")

# 10. Commands strip
cmd = "ansible-inventory --graph (run first: shows the nesting at a glance), --list, --host gpu01"
print(f"CMD '{cmd}': {est_w(cmd, 24, True):.1f} px (avail in 1520px: {1520 - est_w(cmd, 24, True):.1f} px)")

# 11. Warning strip
warn = "a node missing from the inventory quietly misses every change you make"
print(f"WARN '{warn}': {est_w(warn, 24, False):.1f} px (avail in 1520px: {1520 - est_w(warn, 24, False):.1f} px)")

# 12. Bottom bar
bot = "The inventory is the phone book of your fleet"
print(f"BOT '{bot}': {est_w(bot, 26, False):.1f} px (avail in 1520px: {1520 - est_w(bot, 26, False):.1f} px)")

