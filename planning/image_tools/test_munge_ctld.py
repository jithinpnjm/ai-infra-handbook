from verify_full_layout import *

# Let's add MUNGE -> CTLD to paths:
paths = {}
paths['U1->CTLD'] = [(520, 230), (520, 340)]
paths['U2->DBD'] = [(1090, 230), (1090, 350)]
paths['BACKUP<->CTLD'] = [(440, 525), (480, 525)]
paths['REST->CTLD'] = [(340, 390), (480, 390)]
paths['CTLD->DBD'] = [(860, 440), (960, 440)]
paths['DBD->DB'] = [(1220, 440), (1270, 440)]
paths['CTLD->D1'] = [(480, 560), (250, 560), (250, 740)]
paths['CTLD->D2'] = [(540, 580), (540, 740)]
paths['CTLD->D3'] = [(830, 580), (830, 740)]
paths['D1->STEPD'] = [(250, 830), (250, 880)]
paths['STEPD->JOB'] = [(250, 980), (250, 1030)]
paths['U1->D1'] = [(140, 180), (60, 180), (60, 785), (130, 785)]
paths['MUNGE->DBD'] = [(1090, 740), (1090, 530)]
paths['MUNGE->CTLD'] = [(1060, 740), (1060, 560), (860, 560)]

# Now let's check MUNGE -> D1:
# Where can MUNGE -> D1 go?
# Let's test routing MUNGE -> D1 around the bottom!
# Compute nodes bottom is at y=1160.
# JOB is at y=1030..1120.
# MUNGE is at y=740..900.
# MUNGE bottom at (1100, 900) -> down to (1100, 1140) -> left to (250, 1140) -> up to JOB? No, target is D1!
# Wait, can MUNGE -> D1 enter D1 directly, or why not place D1 where MUNGE can reach it?
# Let's check!
print("Testing intersections including MUNGE->CTLD:")
for name1, p1 in paths.items():
    for name2, p2 in paths.items():
        if name1 >= name2: continue
        for i in range(len(p1)-1):
            s1_a, s1_b = p1[i], p1[i+1]
            for j in range(len(p2)-1):
                s2_a, s2_b = p2[j], p2[j+1]
                if intersect(s1_a, s1_b, s2_a, s2_b):
                    print(f"INTERSECTION: {name1} seg {i} intersects {name2} seg {j}")
print("Done!")
