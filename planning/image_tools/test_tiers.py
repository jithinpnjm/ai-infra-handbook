# Layout test:
# Col 1 (x ~ 60..260): U (User laptop)
# Col 2 (x ~ 380..720):
#   Row 1: P (Open OnDemand portal)
#   Row 2: B (Bastion / jump host)
#   Row 3: D (Data transfer nodes: Globus, rsync, rclone)
# Col 3 (x ~ 840..1160):
#   Row 1: L (Login nodes)
#   Row 2: S (Slurm controller)
#   Row 3: ST (Parallel file system)
# Col 4 (x ~ 1280..1540):
#   Row 1 or 2: C (Compute nodes)

# Let's trace every edge:
# 1. U -> B: Col 1 to Col 2 (Row 2).
# 2. U -> P: Col 1 to Col 2 (Row 1).
# 3. U -> D: Col 1 to Col 2 (Row 3).
# All 3 edges from U branch out cleanly without crossing!

# 4. B -> L: B (Col 2, Row 2) to L (Col 3, Row 1).
#    Wait! If B is at Row 2 and L is at Row 1, B -> L goes up-right.
#    What about P -> L? P is at Col 2, Row 1, and L is at Col 3, Row 1.
#    P -> L goes horizontally to L.
#    Wait! If P is at Row 1 and B is at Row 2, then B -> L goes up-right into L,
#    while P -> L goes horizontally into L.
#    Wait, does B -> L cross P -> L?
#    No, P -> L enters the left/top of L, B -> L enters the bottom/left of L.
#    BUT wait, what if B is at Row 1 and P is at Row 2?
#    Let's check:
#    If B is at Row 1 (top):
#      U -> B (Row 1)
#      B -> L (Row 1 to Row 1: straight horizontal!)
#    If P is at Row 2:
#      P -> L (Row 2 to Row 1: up-right into bottom of L!)
#      P -> C (Row 2 to Col 4: straight horizontal across to C!)
#      Wait! If P -> C goes from Col 2, Row 2 across to Col 4 (Compute nodes),
#      what is in Col 3, Row 2? S (Slurm controller)!
#      Can an arrow pass through S?
#      RULE: "Arrows must never cross each other, never pass through a node, and never cross a text label."
#      So P -> C cannot pass through S!
#      Therefore, P cannot go through S.

print("Need to route around S or position nodes properly.")
