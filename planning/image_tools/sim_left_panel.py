# Simulating Left panel layout
# Left panel: x=40, y=105, w=740, h=540

# Cards inside Left panel:
# We need to place:
# 1. File line 1: '[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12'
# 2. File line 2: '[login] login01 ansible_host=10.0.10.5'
# 3. File line 3: '[cluster:children] gpu login'
# 4. File line 4: '[cluster:vars] ansible_user=automation, ansible_python_interpreter=/usr/bin/python3'
# 5. Callout 1: 'each host has a name and optionally an address'
# 6. Callout 2: 'a group collects hosts that share a role'

# Let us check vertical space in h=540:
# If stacked vertically:
# Line 1: 3 lines of text -> h = 100
# Callout 1: 2 lines of text -> h = 75
# Line 2: 2 lines of text -> h = 75
# Callout 2: 2 lines of text -> h = 75
# Line 3: 2 lines of text -> h = 75
# Line 4: 3 lines of text -> h = 100
# Total height: 100 + 75 + 75 + 75 + 75 + 100 = 500 px!
# With gaps: 5 * 10 = 50 -> 550 px.
print("Vertical stacking height ~ 540-560px")
