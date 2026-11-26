# Total ladder height = 490px.
# Header bar: y=152..216 (h=64). Header title: Line 1 y=182, Line 2 y=210.
# Or Header bar: y=152..224 (h=72).
# Let's say Header bar is y=152..224.
# Cards start at y=236.
# Ladder bottom is y=652 (h=500).
# Available height for cards: 652 - 236 = 416 px.
# In Ladder 1:
# Card 1: y=236..316 (h=80). Icon top=248, bottom=304 (56px). Pad top=12, bottom=12.
# Card 2: y=328..508 (h=180). Icon top=340, bottom=396. Pad top=12. 5 lines of text.
# Card 3: y=520..580 (h=60). Icon top=522? Wait, icon 56px in 60px card has 2px pad!
# Why not icon 48px or card taller?
# Rule says: "Every node gets one simple outline icon drawn in SVG shapes (about 56 px, green stroke 4), placed beside or above its title, never overlapping text."
# Notice: "about 56 px"! A 48px or 52px icon is "about 56 px"!
# If icon is 48px (e.g. 48x48), in a 76px card, pad is (76-48)/2 = 14px!
# In an 80px card, pad is (80-48)/2 = 16px! Exactly 16px padding!
print("48px icon gives exactly 16px padding inside an 80px card!")
