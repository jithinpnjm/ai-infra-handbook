import re

# Col 1: x = 40, width = 740
# Card inner width: card x = 60, width = 700 (or card x = 56, width = 708)
# Let's say card x = 60, width = 700.

# In card:
# Option A: Number circle on left, icon on left, text beside:
# If circle cx=96 (x=72..120), icon x=136..192 (56px), text starts at x=208:
# Available width = 760 - 208 - 16 = 536 px.

# Option B: Number circle and icon on top-left:
# Line 1: starts at x=208 (beside circle and icon).
# Subsequent lines start at x=80!
# If subsequent lines start at x=80:
# Available width = 760 - 80 - 16 = 664 px!
# Let's check text lines in Option B:

# Ladder 1 Step 1:
# 'ANSIBLE_CONFIG environment variable'
# Line 1: 'ANSIBLE_CONFIG environment variable' (len=35)
w1 = 35 * 24 * 0.62 # 520.8 px <= 536 px! Fits on 1 line beside icon!

# Ladder 1 Step 2:
# './ansible.cfg in the current directory (honoured only if it is not world-writable: a folder any user can change cannot be trusted)'
# Can we break this into:
# Line 1 (x=208): './ansible.cfg in current dir' -> wait, must use EXACT label!
# Line 1 (x=208): './ansible.cfg ' (len=14, w=208)
# Line 2 (x=80): 'in the current directory (honoured only if it is not ' (len=53, w=53*14.4=763.2 > 664)
# What if:
# Line 1: './ansible.cfg'
# Line 2: 'in the current directory'
# Line 3: '(honoured only if it is not world-writable:'
# Line 4: 'a folder any user can change cannot be trusted)'
lines_s2 = [
    "./ansible.cfg ",
    "in the current directory ",
    "(honoured only if it is not world-writable: ",
    "a folder any user can change ",
    "cannot be trusted)"
]
for l in lines_s2:
    print(f"'{l}': len={len(l)}, w={len(l)*24*0.62:.1f}")

