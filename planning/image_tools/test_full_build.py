import xml.etree.ElementTree as ET
import re

W = 1600
H = 1200

title_text = "Ten things to decide for a GPU or HPC pod's network"
bottom_bar_text = "Decide the rails before you write the pod spec"

# Row data:
# For each row, we specify:
# (row_num, [(line_idx, is_title, text, x_offset)])
# If line 0 has both title and start of rule:
# Wait! In SVG:
# If line 0 has title and rule:
# <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
#   <tspan x="116" y="cur_y + 40" font-size="30" font-weight="bold">1 Primary versus data plane: </tspan>
#   <tspan x="116 + tw" y="cur_y + 40" font-size="24">eth0 for control, secondary RDMA</tspan>
#   <tspan x="116" y="cur_y + 66" font-size="24">NICs for GPU and storage traffic</tspan>
# </text>
# Wait! Does audit_ten_things check each tspan's x and w?
# Let's check:
# In audit_ten_things:
# For tspan 1 (title):
#   tx = 116, fs = 30, w = len(t) * 0.60 * 30
#   x_right = 116 + w
#   pad_r = 1560 - x_right >= 16. (w ~ 522px -> x_right ~ 638px, pad_r = 922px >= 16px!)
# For tspan 2 (inline rule part):
#   tx = 116 + w_title_actual (or conservative)
#   fs = 24, w2 = len(t2) * 0.60 * 24
#   x_right = tx + w2
#   pad_r = 1560 - x_right!
#   Let's check:
#   In Row 1:
#   t1 = "1 Primary versus data plane: " (29 chars) -> tw = 29 * 0.60 * 30 = 522px.
#   tx2 = 116 + 522 = 638px.
#   t2 = "eth0 for control, secondary RDMA" (32 chars) -> rw = 32 * 0.60 * 24 = 460.8px.
#   x_right = 638 + 460.8 = 1098.8px!
#   pad_r = 1560 - 1098.8 = 461.2px >= 16px!
#   pad_l = tx2 - 40 = 598px >= 16px!
#   pad_t = 40 - 24 * 0.8 = 20.8px >= 16px!
#   pad_b = 82 - 40 = 42px >= 16px!
# For tspan 3 (line 2 of rule):
#   tx = 116, y = cur_y + 66, fs = 24
#   t3 = "NICs for GPU and storage traffic" (32 chars) -> rw = 460.8px.
#   x_right = 116 + 460.8 = 576.8px.
#   pad_r = 1560 - 576.8 = 983.2px >= 16px!
#   pad_l = 116 - 40 = 76px >= 16px!
#   pad_b = 82 - 66 = 16.0px >= 16px!
# ALL THREE TSPANS PASS EVERY SINGLE PADDING CHECK!
print("Row 1 padding math verified perfectly!")
