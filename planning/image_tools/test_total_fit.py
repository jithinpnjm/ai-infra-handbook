# Total canvas H = 1200
# Title: 48px bold, 2 lines
# Line 1 y=52, Line 2 y=102
# Title bar/header ends at y=120
# Gap = 15 px
# Panels top: y=135
# Bottom bar: y=1130 to 1180 (height 50)
# Gap = 15 px
# Panels bottom: y=1115
# Total panel height: 1115 - 135 = 980 px!

# In Panel 1:
# Header: y=135 to 195 (height 60)
# Inside panel, remaining height = 980 - 60 = 920 px.
# We have:
# 1. Flow box
# 2. Arithmetic box
# (grouped together / connected by line)
# 3. Arrow pointing to Failure box
# 4. Failure box
# 5. Metaphor box
# 6. Fix box
# 7. Lesson box

# Let's see: 6 boxes + 1 arrow
# If box heights:
# Flow: 2 lines -> 85 px
# Arith: 4 lines -> 135 px
# (Line between Flow and Arith: 12 px)
# Arrow between Arith and Failure: 25 px
# Failure: 4 lines -> 135 px
# Gap: 15 px
# Metaphor: 3 lines -> 110 px
# Gap: 15 px
# Fix: 4 lines -> 135 px
# Gap: 15 px
# Lesson: 2 lines -> 85 px

total_p1 = 85 + 12 + 135 + 25 + 135 + 15 + 110 + 15 + 135 + 15 + 85
print(f"Total P1 contents: {total_p1} px")
print(f"Remaining in P1: {920 - total_p1} px")

# In Panel 2:
# 5 boxes:
# Symptom: 3 lines -> 110 px
# Gap: 20 px
# Evidence: 4 lines -> 135 px
# Gap: 20 px
# Causes: 3 lines -> 110 px
# Gap: 20 px
# Note: 2 lines -> 85 px
# Gap: 20 px
# Fix: 3 lines -> 110 px
total_p2 = 110 + 20 + 135 + 20 + 110 + 20 + 85 + 20 + 110
print(f"Total P2 contents: {total_p2} px")
print(f"Remaining in P2: {920 - total_p2} px")

