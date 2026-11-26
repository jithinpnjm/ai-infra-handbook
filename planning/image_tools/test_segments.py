from verify_full_layout import *

# Let's define the paths of all 15 connections:

paths = {}

# 1. U1 -> CTLD ("RPC + munge credential")
# U1 bottom at x=520, y=230 -> CTLD top at x=520, y=340
paths['U1->CTLD'] = [(520, 230), (520, 340)]

# 2. U2 -> DBD ("RPC")
# U2 bottom at x=1090, y=230 -> DBD top at x=1090, y=350
paths['U2->DBD'] = [(1090, 230), (1090, 350)]

# 3. CTLD <-> BACKUP
# BACKUP right at x=440, y=525 -> CTLD left at x=480, y=525
paths['BACKUP<->CTLD'] = [(440, 525), (480, 525)]

# 4. REST -> CTLD
# REST right at x=340, y=390 -> CTLD left at x=480, y=390
paths['REST->CTLD'] = [(340, 390), (480, 390)]

# 5. CTLD -> DBD ("job and usage records")
# CTLD right at x=860, y=440 -> DBD left at x=960, y=440
paths['CTLD->DBD'] = [(860, 440), (960, 440)]

# 6. DBD -> DB
# DBD right at x=1220, y=440 -> DB left at x=1270, y=440
paths['DBD->DB'] = [(1220, 440), (1270, 440)]

# 7. CTLD -> D1 ("launch and control RPCs")
# CTLD bottom at x=530, y=580 -> down to (530, 650) -> left to (250, 650) -> down to D1 top at (250, 740)
paths['CTLD->D1'] = [(530, 580), (530, 650), (250, 650), (250, 740)]

# 8. CTLD -> D2
# CTLD bottom at x=600, y=580 -> down to (600, 665) -> left to (540, 665) -> down to D2 top at (540, 740)
# Wait, let's keep CTLD->D2 to the right of CTLD->D1:
# CTLD at x=600 -> D2 top at (540, 740).
# Let's check: CTLD bottom x=580 -> (580, 670) -> (540, 670) -> (540, 740).
# Wait, let's see: CTLD->D1 turns left at y=640 to x=250.
# So CTLD->D1 uses x in [250, 530] at y=640.
# If CTLD->D2 turns left at y=670: it would cross CTLD->D1's vertical segment if x=530 < x=580!
# WAIT! Look at that:
# CTLD->D1 starts at x=530, goes down to y=640, then left to x=250, then down to y=740.
# If CTLD->D2 is at x=540: D2 is at x=540!
# Why not have CTLD->D1 start at x=500?
# CTLD->D1: start at x=500 -> (500, 640) -> (250, 640) -> (250, 740).
# CTLD->D2: start at x=600 -> (600, 670) -> (540, 670) -> wait!
# If CTLD->D2 starts at x=540, it can just go STRAIGHT DOWN from (540, 580) to (540, 740)!
# And CTLD->D3: D3 is at x=830, CTLD is x in [480, 860].
# CTLD->D3 can just go STRAIGHT DOWN from (830, 580) to (830, 740)!
# And CTLD->D1: D1 is at x=250.
# If CTLD->D1 leaves CTLD at left edge (x=480, y=560) -> goes left to (250, 560) -> goes down to (250, 740)!
# Let's check that!

paths['CTLD->D1'] = [(480, 560), (250, 560), (250, 740)]
paths['CTLD->D2'] = [(540, 580), (540, 740)]
paths['CTLD->D3'] = [(830, 580), (830, 740)]

# 9. D1 -> STEPD
paths['D1->STEPD'] = [(250, 830), (250, 880)]

# 10. STEPD -> JOB ("runs your program")
paths['STEPD->JOB'] = [(250, 980), (250, 1030)]

# 11. U1 -> D1 ("srun talks to slurmd and slurmstepd directly")
# Leaves U1 left edge at (140, 180) -> left to (60, 180) -> down to (60, 785) -> right into D1 left edge at (130, 785)
paths['U1->D1'] = [(140, 180), (60, 180), (60, 785), (130, 785)]

# 12. MUNGE -> DBD
# MUNGE top at (1090, 740) -> straight up to DBD bottom at (1090, 530)
paths['MUNGE->DBD'] = [(1090, 740), (1090, 530)]

# 13. MUNGE -> D1
# D1 is at x=130..370, y=740..830.
# But wait! D2 and D3 are between D1 and MUNGE!
# D2 is at x=420..660, D3 is at x=710..950.
# How does MUNGE reach D1?
# MUNGE can go along the BOTTOM of Compute nodes!
# Below D2 and D3:
# At y=1075 (next to JOB, or at y=855 between D1/D2/D3 and STEPD?):
# Wait! Look: D1, D2, D3 are row 1 (y=740..830).
# STEPD and JOB are ONLY under D1! (x=130..370).
# The area under D2 and D3 (x in [420, 950], y in [850, 1150]) is COMPLETELY EMPTY!
# Let's verify:
# Under D3 is empty. Under D2 is empty.
# So an arrow from MUNGE (left edge at x=1050, y=860):
# Can go straight left at y=860 to (370, 860) -> into D1 bottom-right edge at (370, 830)!
# OR straight into D1's right edge at (370, 800) if D2/D3 are placed below or above?
# Wait! What if D1 is on the RIGHT of Compute nodes, and D2/D3 are on the LEFT?
# Let's check!

print("Testing intersection between paths:")
for name1, p1 in paths.items():
    for name2, p2 in paths.items():
        if name1 >= name2: continue
        # check each segment
        for i in range(len(p1)-1):
            s1_a, s1_b = p1[i], p1[i+1]
            for j in range(len(p2)-1):
                s2_a, s2_b = p2[j], p2[j+1]
                if intersect(s1_a, s1_b, s2_a, s2_b):
                    print(f"INTERSECTION: {name1} seg {i} intersects {name2} seg {j}")
