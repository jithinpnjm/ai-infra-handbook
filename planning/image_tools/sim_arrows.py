import matplotlib.pyplot as plt

# Let's write the exact coordinates and test arrow routing without crossing.
# Bottom edge of PW is at y=620, x in [560, 1020].
# Outgoing from PW:
# 1. PW -> CRI (done, right edge at y=530)
# 2. PW -> VM
# 3. PW -> DM
# 4. PW -> PR
# 5. PW -> SM

# Incoming to PW:
# 1. PM -> PW (done, top edge at x=790)
# 2. EV -> PW (done, left edge at y=555)
# 3. PLEG -> PW (done, right edge at y=580)

print("PW boundary:")
print("Top: y=490, [560, 1020]")
print("Bottom: y=620, [560, 1020]")
print("Left: x=560, [490, 620]")
print("Right: x=1020, [490, 620]")

