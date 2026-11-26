# Available height = 1200
# Top margin = 40, Bottom margin = 40
# Remaining = 1120

# Let's see:
# Title: y=40, font 48px, 2 lines -> takes y=40 to y=140. (height 100px)
# Gap: 30 or 40px.

# Let's test if H=1200 can accommodate:
# 3 lanes + footer/docker note + bottom bar.
# Lane 1: height ~ 220
# Lane 2: height ~ 320
# Lane 3: height ~ 180
# Footer + Docker note: height ~ 140
# Bottom bar: height ~ 60
# Total = 100 + 40 + 220 + 40 + 320 + 40 + 180 + 40 + 140 + 40 + 60 = 1220!
print("Total with 40px gaps:", 100 + 40 + 220 + 40 + 320 + 40 + 180 + 40 + 140 + 40 + 60)
