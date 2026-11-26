# Let's test a clean, spacious layout:
# Canvas: 1600 x 1200

# y=0..120: Title
# Title L1 y=48, Title L2 y=102. Bounds: 12..114.
# Gap: 114 to 135 = 21px.

# Left and Right Panels: y=135..845 (height=710px)

# LEFT PANEL (x=40..780, w=740, h=710):
# Header: y=150..215 (h=65) -> text y=195, icon y=155..211
# Card 1 (cpustat fields): y=230..375 (h=145)
#   Icon: y=240..296
#   Text: y=275, 315, 355
#   Top: 275 - 18 = 257 (pad_top = 257 - 230 = 27px)
#   Bot: 355 + 6 = 361 (pad_bot = 375 - 361 = 14px -> make h=150: y=230..380, pad_bot=19px!)
# Gap: 380 to 395 = 15px.
# Card 2 (rule): y=395..510 (h=115)
#   Icon: y=415..471
#   Text: y=445, 485
#   Top: 445 - 19 = 426 (pad_top = 426 - 395 = 31px)
#   Bot: 485 + 6 = 491 (pad_bot = 510 - 491 = 19px)
# Gap: 510 to 525 = 15px.
# Card 3 (cadvisor): y=525..670 (h=145)
#   Icon: y=538..594
#   Text: y=620, 656
#   Top: 620 - 18 = 602 (pad_top = 602 - 525 = 77px, icon is above!)
#   Bot: 656 + 6 = 662 (pad_bot = 670 - 662 = 8px -> make text y=615, 650, pad_bot=14px, or h=150: y=525..675, text y=615, 650, pad_bot=19px!)
# Gap: 675 to 690 = 15px.
# Card 4 (psi): y=690..825 (h=135)
#   Icon: y=730..786
#   Text: y=766
#   Top: 766 - 21 = 745 (pad_top = 745 - 690 = 55px)
#   Bot: 766 + 7 = 773 (pad_bot = 825 - 773 = 52px)

print("Left Panel fits with >=19px padding everywhere!")

# RIGHT PANEL (x=820..1560, w=740, h=710):
# Header: y=150..215 (h=65) -> text y=195, icon y=155..211
# Host Box (64 CPUs): y=230..400 (h=170)
#   Host Header: text y=268 (fs=30), icon y=238..294.
#   Container box inside: y=285..385 (h=100)
#     cpu.max text: y=318 (fs=24). Top = 318-18=300 (pad_top = 300-285 = 15px).
#     nproc badge: y=335..375 (h=40). Text y=362 (fs=24). Top = 362-18=344 (pad_top = 344-335 = 9px).
#     Wait! Let's check nproc badge padding.
