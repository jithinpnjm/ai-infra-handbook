# Let's test two parallel orthogonal tracks between IDLE and DOWN:
#
# Track A (IDLE -> DOWN):
# Starts at IDLE (300, 530) [or bottom at (340, 560)]
# Let's say:
# Leaves IDLE at (300, 540)
# (300, 540) -> (100, 540) -> (100, 1020) -> (750, 1020) -> (750, 940) [DOWN bottom]
#
# Track B (DOWN -> IDLE):
# Runs parallel, inside Track A (offset by 60px):
# Starts at DOWN bottom (810, 940)
# (810, 940) -> (810, 960) -> (160, 960) -> (160, 600) -> (300, 600) [IDLE bottom-left]
# Wait, let's trace:
# Track A:
# Horizontal 1: y=540, x from 100 to 300
# Vertical 1:   x=100, y from 540 to 1020
# Horizontal 2: y=1020, x from 100 to 750  (LENGTH = 650px)
# Vertical 2:   x=750, y from 940 to 1020
#
# Track B:
# Leaves DOWN at (800, 940) or (750, 860) [top of DOWN]
# What if Track B leaves DOWN top at (750, 860)?
# Goes up to y=700: (750, 860) -> (750, 700) -> (160, 700) -> (160, 520) -> (300, 520)?
# Wait, if Track B has x=160 and y=700, and Track A has x=100 and y=1020:
# Track A is at x=100 (outer), Track B is at x=160 (inner).
# Horizontal of Track B is at y=700.
# Horizontal of Track A is at y=1020.
# Do they cross?
# Track A vertical is at x=100. Track B horizontal is from x=160 to 750.
# 100 is NOT in [160, 750]!
# Track A horizontal is at y=1020. Track B vertical is from y=520 to 700.
# 1020 is NOT in [520, 700]!
# ZERO INTERSECTIONS!

print("Track A and Track B do NOT intersect!")
