# Test title wrap and vertical budget:
# Title:
# <tspan x="800" dy="0">Reading facts: </tspan>
# <tspan x="800" dy="50">three setup commands and the facts list</tspan>
# y_title = 48 -> dy=50 -> second line at y=98.
# Box starts at y = 130 (gap 32px after title baseline, or let's check).
# If Section 1 starts at y = 130:
# Section 1 ends at 130 + 380 = 510.
# Gap: 40px -> Section 2 (Example box) starts at 550.
# Section 2 height: let's see:
# Can Section 2 be 200px? (550 to 750)
# Gap: 40px -> Section 3 (Prefer strip) starts at 790.
# Section 3 height: 120px (790 to 910).
# Gap: 40px -> Section 4 (Cost strip) starts at 950.
# Section 4 height: 90px (950 to 1040).
# Gap: 40px -> Section 5 (Bottom bar) starts at 1080.
# Section 5 height: 70px (1080 to 1150).
# Bottom margin: 1200 - 1150 = 50px!
# Everything fits with >= 40px gaps and >= 40px margins!

y1 = 130
h1 = 380
y2 = y1 + h1 + 40 # 550
h2 = 200
y3 = y2 + h2 + 40 # 790
h3 = 120
y4 = y3 + h3 + 40 # 950
h4 = 90
y5 = y4 + h4 + 40 # 1080
h5 = 70
y_end = y5 + h5 # 1150
margin_bottom = 1200 - y_end # 50px

print("y1:", y1, "h1:", h1)
print("y2:", y2, "h2:", h2)
print("y3:", y3, "h3:", h3)
print("y4:", y4, "h4:", h4)
print("y5:", y5, "h5:", h5)
print("y_end:", y_end, "bottom margin:", margin_bottom)
