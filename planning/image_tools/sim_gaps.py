# Let's see if H can be 1200 or larger:
# Prompt says: "Use H=900, or up to 1200 if the content needs more room."
# Does H=1200 support 40px gaps?
# Let's check:
# Title: y=40..115 (text, not a box)
# Gap title to box 1: 40px -> box 1 at y=155
# Wait, what if Host container IS the box?
# If Host is a large outer box, and lanes are inside it?
# Or if each Lane is a box?
# Let's count boxes if they are separate:
# If Host top bar: h=70
# gap: 40
# Lane 1: h=180
# gap: 40
# Lane 2: h=280
# gap: 40
# Lane 3: h=140
# gap: 40
# Footer/Docker: h=150
# gap: 40
# Bottom bar: h=50
# Margin bottom: 40
# Total: 155 + 70 + 40 + 180 + 40 + 280 + 40 + 140 + 40 + 150 + 40 + 50 + 40 = 1225!
print(155 + 70 + 40 + 180 + 40 + 280 + 40 + 140 + 40 + 150 + 40 + 50 + 40)
