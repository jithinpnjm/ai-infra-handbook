from verify_full_layout import *

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
# MUNGE -> D1:
paths['MUNGE->D1'] = [(1050, 855), (350, 855), (350, 830)]

print("Checking ALL 15 connections for ANY intersection:")
intersections = 0
for name1, p1 in paths.items():
    for name2, p2 in paths.items():
        if name1 >= name2: continue
        for i in range(len(p1)-1):
            s1_a, s1_b = p1[i], p1[i+1]
            for j in range(len(p2)-1):
                s2_a, s2_b = p2[j], p2[j+1]
                if intersect(s1_a, s1_b, s2_a, s2_b):
                    print(f"INTERSECTION: {name1} seg {i} intersects {name2} seg {j}")
                    intersections += 1
if intersections == 0:
    print("PERFECT! ALL 15 CONNECTIONS ARE 100% NON-INTERSECTING!")
