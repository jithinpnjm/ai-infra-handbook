# Let's explore node assignments in a 2-column or 3-column system:
#
# Nodes:
# I: IDLE
# A: ALLOCATED
# Dg: DRAINING
# Dd: DRAINED
# Dw: DOWN
#
# Edges:
# S -> I
# I <-> A (2)
# I <-> Dd (2)
# A -> Dg (1)
# Dg -> Dd (1)
# I <-> Dw (2)
# A -> Dw (1)
#
# What if:
# Column 1 (Left):   Dd (DRAINED), I (IDLE)
# Column 2 (Middle): Dg (DRAINING), A (ALLOCATED)
# Column 3 (Right):  Dw (DOWN)
#
# Let's check:
# Top row:    I (col 1), A (col 2), Dw (col 3)
# Bottom row: Dd (col 1), Dg (col 2)
#
# Let's trace every edge:
# 1. [*] -> I: from left into I.
# 2. I <-> A: between col 1 and col 2 (top row).
# 3. A <-> Dw:
#    - A -> Dw: between col 2 and col 3 (top row).
# 4. I <-> Dw:
#    Wait! I is col 1, Dw is col 3.
#    Edges:
#    - I -> Dw: "slurmd not responding..."
#    - Dw -> I: "resume or ReturnToService..."
#    Can they go above I, A, Dw?
#    Yes! Across the top banner from col 1 to col 3!
#    Distance from col 1 (x=250) to col 3 (x=1350) is 1100px!
# 5. A -> Dg: vertical down from col 2 top to col 2 bottom!
# 6. Dg -> Dd: horizontal left from col 2 bottom to col 1 bottom!
# 7. I <-> Dd: vertical up/down between col 1 top and col 1 bottom!
#
# DO ANY EDGES CROSS?
# Let's check:
# Top band (above top row): I <-> Dw (2 arrows).
# Top row: I <-> A, and A -> Dw.
# Bottom row: Dg -> Dd.
# Vertical:
# Col 1: I <-> Dd.
# Col 2: A -> Dg.
#
# Look at that:
# Col 1 vertical (I <-> Dd) does NOT cross Col 2 vertical (A -> Dg)!
# Top band does NOT cross anything!
# Bottom row does NOT cross anything!
# ZERO CROSSINGS!
print("ZERO CROSSINGS IN 3-COLUMN LAYOUT!")
