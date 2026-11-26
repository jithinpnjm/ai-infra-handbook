# Let's calculate:
# Can we make:
# Canvas: 1600 x 1200.
# y=0:
# Title at y=50, fs=48 (top=50-36=14 or y=54, top=18)
# Subtitle Pill:
#   y=68, h=56, rx=28.
#   text at y=104, fs=24:
#   pad_top = 104 - 18 - 68 = 18px >= 16px!
#   pad_bottom = (68+56) - (104 + 5.28) = 124 - 109.28 = 14.72px.
#   What if h=58, y=66..124? Text at y=103:
#   pad_top = 103 - 18 - 66 = 19px.
#   pad_bottom = 124 - (103 + 5.28) = 15.72px.
#   What if h=60, y=66..126? Text at y=104:
#   pad_top = 104 - 18 - 66 = 20px >= 16px.
#   pad_bottom = 126 - (104 + 5.28) = 16.72px >= 16px.
#   Bottom of pill = 126.

# Outside margin: >= 40px.
# Gap to Setup Box: 40px -> Setup starts at y = 126 + 40 = 166.
# Setup Box:
#   rect x=50, y=166, w=1500, h=94
#   Icon: 75, 185, 56x56
#   Text: line 1 y=205, line 2 y=238.
#   pad_top = 205 - 18 - 166 = 21px >= 16px.
#   pad_bottom = (166+94) - (238 + 5.28) = 260 - 243.28 = 16.72px >= 16px.
#   Setup bottom = 260.

# Gap to Table 1: 40px -> Table 1 starts at y = 260 + 40 = 300.
# Table 1:
# Header:
#   rect: y=312, h=56.
#   text: "Table 1 policy: hit rate, p50 s, p99 s, max over mean load", fs=30.
#   text y=351:
#   pad_top = 351 - 0.75*30 - 312 = 351 - 22.5 - 312 = 16.5px >= 16px!
#   pad_bottom = (312+56) - (351 + 0.22*30) = 368 - 357.6 = 10.4px.
#   Wait! Let's check pad_bottom for text in the check script:
#   In check_all_paddings_strict.py:
#   pad_top = (baseline_y - fs) - box_y
#   pad_bottom = (box_y + box_h) - baseline_y
#   Wait!! Look at how check_all_paddings_strict.py defined pad_bottom:
#   pad_bottom = (box_y + box_h) - baseline_y!
#   IT USES BASELINE_Y, NOT BASELINE_Y + DESCENT!
#   Let's check if other check scripts use baseline_y or descent:
print("Let's check how all check scripts in repo define pad_top and pad_bottom!")
