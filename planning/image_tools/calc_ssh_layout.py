#!/usr/bin/env python3
import pathlib

# Let's test the layout where:
# - Title has padding >= 16px from canvas bounds
# - All boxes have height >= font_size + 32 (or font_size + dy + 32)
# - text_y = box_y + 16 + font_size
# - center_x = box_x + box_width / 2

# Dimensions:
# Canvas: 1600 x 1200
# Header container: x=60, y=140, w=1480, h=155
#   Your machine box: x=80, y=148, w=410, h=64
#     text: fs=30, tx=285, ty=194 (padT=16, padB=18, padL=97, padR=97)
#     icon: x=95, y=152, 56x56
#   Server box: x=1110, y=148, w=410, h=64
#     text: fs=30, tx=1315, ty=194 (padT=16, padB=18, padL=151, padR=151)
#     icon: x=1125, y=152, 56x56
#   SSH connection badge: x=600, y=151, w=400, h=58
#     text: fs=24, tx=800, ty=191 (padT=16, padB=18, padL=34.4, padR=34.4)
#   Which side listens? box: x=80, y=222, w=690, h=64
#     text: fs=30, tx=425, ty=268 (padT=16, padB=18, padL=174, padR=174)
#   Where does the traffic go? box: x=830, y=222, w=690, h=64
#     text: fs=30, tx=1175, ty=268 (padT=16, padB=18, padL=111, padR=111)

# Gaps:
# Header (140 to 295) -> Lane 1 (335): gap = 40px
# Lane 1 (335 to 545) -> Lane 2 (585): gap = 40px
# Lane 2 (585 to 795) -> Lane 3 (835): gap = 40px
# Lane 3 (835 to 1045) -> Footer (1085): gap = 40px
# Footer (1085 to 1155) -> Canvas bottom (1200): margin = 45px

# Lane contents:
# In each lane:
# Tag: x=80, y=y_lane+12, w=320, h=60
#   text: fs=28, tx=240, ty=y_lane+56 (padT=16, padB=16, padL=25.6)
# Command: x=420, y=y_lane+14, w=570, h=56
#   text: fs=24, tx=705, ty=y_lane+54 (padT=16, padB=16, padL=39.5)

# Lane 1 bottom:
# Left Box (Orange listening marker): x=80, y=415, w=360, h=110
#   text 'listens on 6006': fs=28, tx=260, ty=475 (padT=32, padB=50, padL=54, padR=54)
# Right Box (Destination): x=1160, y=415, w=360, h=110
#   text 'localhost:6006 on gpu01': fs=26, tx=1340, ty=475 (padT=34, padB=50, padL=17, padR=17)
# Note Box (Center-bottom): x=460, y=455, w=680, h=60
#   text 'open http://localhost:6006 to reach TensorBoard': fs=24, tx=800, ty=495 (padT=16, padB=20, padL=21.6, padR=21.6)

# Lane 2 bottom:
# Left Box (Destination): x=80, y=665, w=420, h=110
#   text 'localhost:8000 on your machine':
#   line 1: 'localhost:8000' fs=26, tx=290, ty=715
#   line 2: 'on your machine' fs=26, tx=290, dy=30 (ty=745)
#   padT = (715 - 26) - 665 = 24px, padB = (665 + 110) - 745 = 30px
#   tw = 234px -> padL = (290 - 117) - 80 = 93px >= 16px
# Right Box (Listening marker): x=1100, y=665, w=420, h=110
#   text 'listens on 9000': fs=28, tx=1310, ty=727 (padT=34, padB=48, padL=84, padR=84)

# Lane 3 bottom:
# Left Box (Listening marker): x=80, y=915, w=420, h=110
#   text 'SOCKS proxy on 1080': fs=28, tx=290, ty=977 (padT=34, padB=48, padL=50, padR=50)
# Right Box (Destination): x=1050, y=915, w=470, h=110
#   text 'traffic goes through bastion to any destination':
#   line 1: 'traffic goes through bastion' fs=24, tx=1285, ty=965
#   line 2: 'to any destination' fs=24, tx=1285, dy=28 (ty=993)
#   padT = (965 - 24) - 915 = 26px, padB = (915 + 110) - 993 = 32px
#   tw1 = 403.2px -> padL = (1285 - 201.6) - 1050 = 33.4px >= 16px!

print("Layout parameters calculated.")
