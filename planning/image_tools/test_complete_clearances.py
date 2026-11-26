# Let's test clearances between all elements in this layout:

# Elements to check:
# 1. State boxes:
# IDLE:      [230..530, 215..305]
# ALLOCATED: [1070..1370, 215..305]
# DRAINED:   [230..530, 515..605]
# DRAINING:  [1070..1370, 515..605]
# DOWN:      [750..1050, 900..990]

# 2. Transition label boxes:
# B_starts:  cx=800, cy=235, w=190, h=44 -> [705..895, 213..257]
# B_ends:    cx=800, cy=285, w=160, h=44 -> [720..880, 263..307]
# B_finish:  cx=800, cy=560, w=320, h=44 -> [640..960, 538..582]
# B_drain:   cx=800, cy=455, w=480, h=44 -> [560..1040, 433..477]
# B_resume:  cx=650, cy=375, w=270, h=44 -> [515..785, 353..397] (wait, IDLE right edge is 530, so let cx=680 -> [545..815])
# B_fail:    cx=1255, cy=730, w=590, h=44 -> [960..1550, 708..752]
# B_down:    cx=480, cy=1020, w=690, h=44 -> [135..825, 998..1042]
# B_rts:     cx=490, cy=810, w=720, h=44 -> [130..850, 788..832]

# Arrows:
# A1 ([*]->IDLE): (95..230, y=225)
# A2 (IDLE->ALLOCATED): y=235, x in [530..1070]
# A3 (ALLOCATED->IDLE): y=285, x in [530..1070]
# A4 (IDLE->DRAINED): x=330, y in [305..515]
# A5 (DRAINED->IDLE): x=450, y in [305..515]
# A6 (ALLOCATED->DRAINING): x=1220, y in [305..515]
# A7 (DRAINING->DRAINED): y=560, x in [530..1070]
# A8 (ALLOCATED->DOWN):
#    (1370, 260) -> (1560, 260) -> (1560, 730) -> (980, 730) -> (980, 900)
# A9 (IDLE->DOWN):
#    (230, 290) -> (60, 290) -> (60, 1020) -> (900, 1020) -> (900, 990)
# A10 (DOWN->IDLE):
#    (820, 900) -> (820, 810) -> (140, 810) -> (140, 260) -> (230, 260)

print("Testing geometry...")
