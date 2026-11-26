import re
import xml.etree.ElementTree as ET

def build_svg():
    H = 1200
    centers = {
        "U": 148.0,
        "A": 311.0,
        "S": 474.0,
        "K": 637.0,
        "R": 800.0,
        "C": 963.0,
        "V": 1126.0,
        "D": 1289.0,
        "X": 1452.0
    }
    
    # Headers
    headers = [
        # Row 1 (y=54..134)
        {"id": "U", "row": 1, "cx": 148.0, "lines": [("User / ", 0), ("controller", 25)], "icon": "window"},
        {"id": "S", "row": 1, "cx": 474.0, "lines": [("Scheduler", 14)], "icon": "clock"},
        {"id": "R", "row": 1, "cx": 800.0, "lines": [("containerd ", 0), ("(CRI)", 25)], "icon": "box"},
        {"id": "V", "row": 1, "cx": 1126.0, "lines": [("CSI node ", 0), ("plugin", 25)], "icon": "cylinder"},
        {"id": "X", "row": 1, "cx": 1452.0, "lines": [("runc / ", 0), ("kernel", 25)], "icon": "terminal"},
        # Row 2 (y=142..222)
        {"id": "A", "row": 2, "cx": 311.0, "lines": [("API server ", 0), ("(+etcd)", 25)], "icon": "lock"},
        {"id": "K", "row": 2, "cx": 637.0, "lines": [("Kubelet", 14)], "icon": "gear"},
        {"id": "C", "row": 2, "cx": 963.0, "lines": [("CNI ", 0), ("plugin", 25)], "icon": "network"},
        {"id": "D", "row": 2, "cx": 1289.0, "lines": [("Device ", 0), ("plugin", 25)], "icon": "chip"}
    ]

    # Steps definition
    # Notice: 
    # Step 1: cy = 264. Card above (232..260).
    # Step 2: cy = 306. Card above (274..302). Circle at (311, 306).
    # Step 3: Arrow at cy = 352. Card BELOW arrow: y = 356..406, x = 184..440.
    #         Circle 2 is at y=306 (bottom 330 < 356). No collision!
    #         Circle 3 is at x=474 (left edge 450 > 440). No collision!
    # Step 4: Arrow at cy = 442. Card ABOVE arrow: y = 410..438, x = 345..769.
    #         Card top is 410 > bottom of Card 3 (406). No collision!
    #         Card top 410 > bottom of Circle 3 (376). No collision!
    # Step 5: Self loop at cy = 492. Card to right: y = 442..492, x = 705..1191.
    # Step 6: Allocate(GPU devices) at cy = 538. Card above: y = 506..534, x = 671..1340. (Orange!)
    # Step 7: NodeStageVolume at cy = 584. Card above: y = 552..580, x = 671..1311.
    # Step 8: RunPodSandbox at cy = 630. Card above: y = 598..626, x = 671..894.
    # Step 9: ADD (netns...) at cy = 676. Circle 9 at (800, 676). Card above: y = 644..672, x = 834..1201.
    # Step 10: PullImage at cy = 724. Card BELOW arrow: y = 728..756, x = 671..1067.
    #          Circle 9 is at cy=676 (bottom 700 < 728). No collision!
    # Step 11: CreateContainer at cy = 770. Card ABOVE arrow: y = 738..766, x = 671..1513.
    #          Wait! If Card 10 is below arrow 10 (y=728..756) and Card 11 is above arrow 11 (y=738..766), they would overlap vertically!
    #          Let's see: what if Card 10 is ABOVE arrow 10, but cy10 is lower?
    #          If cy9 = 668, Circle 9 bottom = 692.
    #          If cy10 = 728, Card 10 above arrow 10 is at y = 728 - 32 = 696..724!
    #          696 > 692!
    #          Then Card 10 sits COMPLETELY BELOW Circle 9 without having to be below the arrow!
    #          Let's check: cy9 = 668, Circle 9 bottom = 692.
    #          Card 10 at y = 696..724 (top 696 > 692). ZERO COLLISION!
    #          And cy10 = 728.
    #          Then Step 11 arrow at cy11 = 776. Card 11 at y = 744..772.
    #          Card 11 top is 744 > Card 10 bottom 724. ZERO COLLISION!
    #          Step 12 at cy12 = 822. Circle 12 at (800, 822). Card 12 at y = 790..818, x = 834..1446.
    #          Step 13 at cy13 = 868. Arrow leftward from 637 to 311.
    #          Card 13 at y = 814..864, x = 47..603.
    #          Circle 13 is at (637, 868). Bottom of Circle 13 is 868 + 24 = 892.
    #          Note over K,X: placed at y = 896..852 (wait, 896..952, height 56).
    #          896 > 892! ZERO COLLISION WITH CIRCLE 13!
    #          Bottom of Note is 896 + 56 = 952.
    #          Step 14 at cy14 = 984. Circle 14 at (148, 984). Top of circle 14 is 960 > 952.
    #          Card 14 at y = 952..980, x = 182..362.
    #          Step 15 at cy15 = 1024. Circle 15 at (311, 1024). Card 15 at y = 992..1020, x = 345..798.
    #          Step 16 at cy16 = 1064. Circle 16 at (637, 1064). Card 16 at y = 1032..1060, x = 671..1153.
    #          Step 17 at cy17 = 1104. Circle 17 at (637, 1104). Card 17 at y = 1072..1100, x = 671..1268.
    #          Wait! Between circle 16 (1064) and circle 17 (1104) the distance is only 40 px!
    #          Circles at the same X must have distance >= 48 px!
    #          Let's make distance >= 48 px!

    print("Checking layout math...")
