# Let's adjust all y coordinates to ensure:
# 1. Canvas margin >= 40 px (top, bottom, left, right)
# 2. Box-to-box gap >= 40 px everywhere
# 3. Text padding inside box >= 16 px everywhere

# Canvas: 1600 x 1200
# Margins:
# Left >= 40, Right <= 1560.
# Top >= 40, Bottom <= 1160.

# Let's budget vertical space from y=40 to 1160 (total: 1120 px):
# y=40..70: Title (48px bold). Baseline at y=60.
# Title top = 60 - 0.8*48 = 21.6. Wait! If margin is 40px, title top must be >= 40px!
# At baseline y=78: title top = 78 - 0.8*48 = 39.6 ~ 40px!
# Title baseline: y=80.
# Title bottom: 80 + 0.2*48 = 89.6.

# Root box:
# Must have gap >= 40px from title? Title is text. Gap between title and root box:
# If root box y = 120: gap = 120 - 89.6 = 30.4 px.
# Let's make root box y = 130!
# Root box: y = 130 .. 226 (height 96).
# Root box: x = 60 .. 1540 (width 1480). Margin left=60 > 40, right=60 > 40.
# Text in root:
# Line 1: baseline y = 170. (top = 170 - 24 = 146, pad from top = 16 px).
# Line 2: baseline y = 204. (bottom = 204 + 4.8 = 208.8, pad from bottom = 17.2 px).
# Root icon at y = 150 (56x56, y from 150 to 206).

# Gap after root box:
# Root box ends at 226.
# Column 1 and 2 start below 226.
# But wait! Condition labels and arrows start right under root box!
# Where do the branch outcome boxes sit?
# If takeaway bar is at bottom:
# Bottom margin = 40 px, so takeaway bottom = 1160.
# Takeaway box: y = 1095 .. 1160 (height 65).
# Takeaway text at y = 1135 (top pad = 19.2px, bottom pad = 19.8px).

# Now, between root box (bottom = 226) and takeaway box (top = 1095):
# Total vertical height = 1095 - 226 = 869 px!
# We need to fit 4 rows in Column 1 and 3 rows in Column 2.
# Box-to-box gap >= 40 px!
# In Column 1, we have 4 boxes: Box 1, Box 2, Box 3, Box 4.
# Gaps between them:
# Gap between Box 1 and Box 2 >= 40 px.
# Gap between Box 2 and Box 3 >= 40 px.
# Gap between Box 3 and Box 4 >= 40 px.
# Gap between Root and Box 1 >= 40 px.
# Gap between Box 4 and Takeaway >= 40 px.

print("Checking feasibility...")
