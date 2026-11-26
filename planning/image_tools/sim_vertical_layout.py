import re

# Canvas: width 1600, height 1200
# Margins: left=40, right=40 (content width = 1520)
# Top margin = 30, bottom margin = 30
# Max H = 1200

# Let's define the vertical slices:
y = 30

# 1. Title (48px bold)
# "Which ansible.cfg wins: the search order and the precedence of settings"
# Line 1: "Which ansible.cfg wins: " (len=24)
# Line 2: "the search order and the precedence of settings" (len=47)
# 47 * 48 * 0.6 = 1353.6 <= 1520 (fits with 83px padding each side)
title_y1 = y + 42 # baseline line 1 (y=72)
title_y2 = title_y1 + 52 # baseline line 2 (y=124)
y = 135

gap1 = 25 # gap to Ladder 1
y += gap1 # y = 160

# 2. Ladder 1 Container: 'Which file is read (first found wins, never merged)'
# Has header + 4 rungs
l1_top = y
# Header height: 38px
# Rung 1: height 54px
# Rung 2: height 68px (2 lines: path + world-writable caveat)
# Rung 3: height 54px
# Rung 4: height 54px
# Gaps between rungs: 10px each (3 gaps = 30px)
# Header gap = 12px
# Container top padding = 12px, bottom padding = 14px
l1_height = 12 + 38 + 12 + 54 + 10 + 68 + 10 + 54 + 10 + 54 + 14 # = 326px
l1_bottom = l1_top + l1_height # y = 486
y = l1_bottom

gap2 = 25
y += gap2 # y = 511

# 3. Ladder 2 Container: 'Which value wins'
# Has header + 4 rungs
l2_top = y
# Header height: 38px
# Rung 1: 52px
# Rung 2: 52px
# Rung 3: 52px
# Rung 4: 52px
# Gaps between rungs: 10px each (3 gaps = 30px)
# Header gap = 12px
# Container top pad = 12px, bottom pad = 14px
l2_height = 12 + 38 + 12 + 52 + 10 + 52 + 10 + 52 + 10 + 52 + 14 # = 314px
l2_bottom = l2_top + l2_height # y = 825
y = l2_bottom

gap3 = 20
y += gap3 # y = 845

# 4. Surprise story (orange)
# 'an engineer runs Ansible from a folder they did not expect, and the tool quietly picks up a different config file'
# 113 chars -> 2 lines
# Line 1: 'an engineer runs Ansible from a folder they did not expect, ' (len=60, w=864)
# Line 2: 'and the tool quietly picks up a different config file' (len=53, w=763)
# Height: 66px
surprise_top = y
surprise_height = 68
surprise_bottom = surprise_top + surprise_height # y = 913
y = surprise_bottom

gap4 = 20
y += gap4 # y = 933

# 5. Commands strip
# 'ansible-config dump --only-changed shows only what you changed; ansible-config list shows every setting with its default; ansible --version shows the config file in use'
# 168 chars -> 2 lines or 3 lines:
# Line 1: 'ansible-config dump --only-changed shows only what you changed; ' (len=64, w=952)
# Line 2: 'ansible-config list shows every setting with its default; ' (len=58, w=863)
# Line 3: 'ansible --version shows the config file in use' (len=46, w=684)
# Or 2 lines!
# Height: 72px (for 2 lines) or 96px (for 3 lines)
commands_top = y
commands_height = 76
commands_bottom = commands_top + commands_height # y = 1009
y = commands_bottom

gap5 = 20
y += gap5 # y = 1029

# 6. Rules strip
# 'keep a project-level ansible.cfg in the repo root; keep secrets and personal paths out of it because it is committed; editing /etc/ansible changes behaviour between laptops and CI and is invisible to Git'
# 3 lines:
# Line 1: 'keep a project-level ansible.cfg in the repo root; ' (len=51, w=734)
# Line 2: 'keep secrets and personal paths out of it because it is committed; ' (len=67, w=964)
# Line 3: 'editing /etc/ansible changes behaviour between laptops and CI and is invisible to Git' (len=85, w=1224)
rules_top = y
rules_height = 92
rules_bottom = rules_top + rules_height # y = 1121
y = rules_bottom

gap6 = 20
y += gap6 # y = 1141

# 7. Bottom bar
# 'Knowing the search order turns a surprise into a quick check'
bottom_top = y
bottom_height = 46
bottom_bottom = bottom_top + bottom_height # y = 1187
y = bottom_bottom

margin_bottom = 1200 - y
print(f"Total height = 1200, bottom margin remaining = {margin_bottom}")
