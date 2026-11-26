# Let's test staircase geometries
# We have 6 steps rising from left to right:
# Step 1, Step 2, Step 3, Step 4, Step 5, Step 6.
# Between each pair of boxes: gate diamond labelled "gates pass"

# Let's check available vertical space:
# Canvas: 1600 x 1200
# Title: y = 35..110
# Gate groups row: y = 150..270 (height 120)
# Gap: 270..330 (60px)
# Staircase area: y = 330..770 (440px height)
# Gap: 770..820 (50px)
# Outcome boxes row: y = 820..1010 (height 190)
# Gap: 1010..1060 (50px)
# Takeaway bar: y = 1060..1120 (height 60)
# Bottom margin: 1120..1200 (80px)

print("Vertical budget:")
print("Title: 35..110")
print("Gate groups: 150..270 (height 120)")
print("Staircase: 330..770 (height 440)")
print("Outcomes: 820..1010 (height 190)")
print("Takeaway: 1060..1120 (height 60)")
