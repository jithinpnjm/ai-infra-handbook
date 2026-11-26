# Total canvas height: up to 1200 (or what if H=1250, 1300? Wait, prompt says: "Use H=900, or up to 1200 if the content needs more room.")
# So H should be <= 1200!
# Available space:
# y = 0 to 1200
# Margin top: 40
# Title: y = 40 to 150 (height = 110)
# Gap: 20
# Grid header: y = 170 to 220 (height = 50)
# Gap: 15
# Available for rows: from y = 235 to y = 1070 (since bottom bar is y = 1090 to 1160, margin 40 at bottom).
# Available height for 5 rows = 1070 - 235 = 835 px!
# With 4 gaps of 12 px (48 px), available for 5 rows is 835 - 48 = 787 px!
# Average height per row = 787 / 5 = 157.4 px!
print(f"Available height per row: {787 / 5:.1f} px")
