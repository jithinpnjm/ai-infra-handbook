# Canvas H = 1200
# Title: y = 40 to 115 (Title baseline 1 at 70, baseline 2 at 115)
# Title height ends around 125.
# Margin after title: gap = 40 -> main section starts at y = 165.

# Bottom bar: y = 1100 to 1160 (h = 60).
# Margin before bottom bar: gap = 40 -> Footnote ends at y = 1060.
# Footnote: y = 920 to 1060 (h = 140).
# Margin before footnote: gap = 40 -> Main section ends at y = 880.

# Main section available vertical range: y = 165 to 880 (height = 715 px)!

# Left column: x = 40 to 500 (width = 460).
# Box 1 (Left box): y = 165 to 445 (height = 280).
# Gap between Box 1 and Box 2: 40 px -> Box 2 starts at y = 485.
# Box 2 (Second box): y = 485 to 880 (height = 395).

# Right container (Column of behaviours):
# x = 740 to 1560 (width = 820).
# y = 165 to 880 (height = 715).

# Arrow: from (500, 305) to (740, 305).
# Length = 240 px.
# Label on arrow: "you get for free"
# Centered at (620, 290) - above the arrow.

print("Vertical budget:")
print(f"Title: 40 to 125 (ends at 125)")
print(f"Gap: 125 to 165 (40 px)")
print(f"Main section: 165 to 880 (715 px)")
print(f"Gap: 880 to 920 (40 px)")
print(f"Footnote: 920 to 1060 (140 px)")
print(f"Gap: 1060 to 1100 (40 px)")
print(f"Bottom bar: 1100 to 1160 (60 px)")
print(f"Canvas margin: 1160 to 1200 (40 px)")
print(f"Total H: 1200 px. All gaps >= 40 px!")

