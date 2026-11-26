#!/usr/bin/env python3

def optimize():
    # Let's compute:
    # 1. Formula box: y=145, h=80 (y: 145..225)
    #    text y = 191 (fs=30, cap~22.5, desc~7.5: top=168.5, bot=198.5. T=23.5, B=26.5) -> OK
    
    # 2. Gap between Formula box and Columns: 40px -> y = 265
    #    Header height: 75px
    #    Left column:
    #      Card 1 (2 lines): y=350, h=94 (y: 350..444)
    #        L1: y=388 (top=370, T=20)
    #        L2: y=422 (bot=428, B=16) -> h=96 gives T=20, B=18
    #      gap: 16px -> y=460
    #      Card 2 (1 line): y=460, h=62 (y: 460..522)
    #        L1: y=498 (top=480, T=20, bot=504, B=18)
    #      gap: 16px -> y=538
    #      Card 3 (3 lines): y=538, h=130 (y: 538..668)
    #        L1: y=576 (top=558, T=20)
    #        L2: y=610
    #        L3: y=644 (bot=650, B=18)
    #      Left column height: (668 + 20) - 265 = 423px -> let's make it y=265..690 (h=425)

    #    Right column: y=265..690 (h=425)
    #      Header: text at y=315 (T=28, B=many)
    #      Card: y=350, h=320 (y: 350..670)
    #        L1: y=390 (top=372, T=22)
    #        L2: y=426
    #        L3: y=462
    #        L4: y=498 (bot=504)
    #        Visual illustration: y=560..600
    #        Bot=600, Card B=670-600=70px -> OK!

    # 3. Gap between Columns and Bottom boxes: 40px -> y = 690 + 40 = 730
    #    Bottom boxes: y=730..1140 (h=410)
    #    Left box (Fixes): y=730..1140
    #      Icon at y=745 (x=68, y=745, w=44, h=44)
    #      Fix 1 (1 line): x=130, y=742, w=630, h=60 (y: 742..802)
    #        text y = 780 (top=762, T=20, bot=786, B=16) -> h=62 gives T=20, B=18
    #      gap: 14px -> y=818
    #      Fix 2 (1 line): x=60, y=818, w=700, h=60 (y: 818..878)
    #        text y = 856 (T=20, B=16) -> h=62 gives T=20, B=18
    #      gap: 14px -> y=894
    #      Fix 3 (1 line): x=60, y=894, w=700, h=60 (y: 894..954)
    #        text y = 932 (T=20, B=16) -> h=62 gives T=20, B=18
    #      gap: 14px -> y=970
    #      Fix 4 (2 lines): x=60, y=970, w=700, h=96 (y: 970..1066)
    #        L1: y=1008 (T=20)
    #        L2: y=1042 (bot=1048, B=18)
    #      gap: 14px -> y=1080
    #      Fix 5 (1 line): x=60, y=1080, w=700, h=62 (y: 1080..1142)
    #        text y = 1118 (T=20, B=18)
    #      Total left bottom: ends at 1142. Container y=730..1160 (h=430)

    #    Right box (Checks): y=730..1160 (h=430)
    #      Icon at y=745 (x=848, y=745)
    #      Check 1 (2 lines): x=840, y=805, w=700, h=120 (y: 805..925)
    #        L1: y=847 (top=829, T=24)
    #        L2: y=883 (bot=889, B=36)
    #      gap: 25px -> y=950
    #      Check 2 (3 lines): x=840, y=950, w=700, h=160 (y: 950..1110)
    #        L1: y=994 (top=976, T=26)
    #        L2: y=1030
    #        L3: y=1066 (bot=1072, B=38)
    
    # 4. Canvas height H: 1160 + 40 = 1200!
    #    1200 is <= 1200! Exactly the maximum allowed!
    print("Optimization plan ready, H=1200.")

optimize()
