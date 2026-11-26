#!/usr/bin/env python3

# Let's test different layout designs:
# What if:
# We have 4 columns.
# Can Column 3 and Column 4 be wider than Column 1 and Column 2?
# Let's see:
# Margin left = 40, Margin right = 40.
# Available width = 1520 px.

# If:
# Box 1 (Root /): width = 240 px
# Gap 1: 150 px
# Box 2 (/home): width = 250 px
# Gap 2: 150 px
# Box 3 (/home/alice): width = 340 px
# Gap 3: 150 px
# Box 4 (Inode C): width = 250 px
# Total = 240 + 150 + 250 + 150 + 340 + 150 + 250 = 1520 px!

# Look at Box 3 width = 340 px!
# If Box 3 is 340 px wide:
# Under Table 3: the callout can also be 340 px wide!
# In a 340 px box:
# Available text width with 16 px padding: 340 - 32 = 308 px.
# Max chars at 24 px sans: 308 / 14.4 = 21.3 characters per line!
# Can 'The name lives in the directory; everything else lives in the inode' wrap into lines <= 21 chars?
# Let's check:
text = "The name lives in the directory; everything else lives in the inode"
words = text.split()
lines = []
cur = []
for w in words:
    trial = " ".join(cur + [w])
    if len(trial) <= 21:
        cur.append(w)
    else:
        lines.append(" ".join(cur))
        cur = [w]
if cur:
    lines.append(" ".join(cur))

print("Callout wrapped into lines <= 21 chars:")
for l in lines:
    print(f"   '{l}' ({len(l)} chars, {len(l)*14.4:.1f}px)")
