# Let's check vertical positions:
# Title: y=62
# Host box: y=95 to 1160 (H=1065)
#   Outside margin: top 95, bottom 1200-1160=40, left 50, right 50. All >= 40!

# Inside Host:
# Callout: x=250, y=112, w=1270, h=60.
# Gap between Callout (bottom 172) and Namespace boxes (top 215): 215 - 172 = 43px >= 40px!

# Top boxes (red and default):
# y = 215 to 720 (height = 505)
#   Inside red and default:
#   Header: icon & label at y=230 (baseline 265)
#   Items (h=46, gap=10):
#   Item 1: y = 285..331
#   Item 2: y = 341..387
#   Item 3: y = 397..443
#   Item 4: y = 453..499
#   Item 5: y = 509..555
#   Item 6: y = 565..611
#   Item 7: y = 621..667
#   Box bottom: 720. Padding below item 7: 720 - 667 = 53px.

# Gap between Top boxes (bottom 720) and Bottom boxes:
# Bottom boxes start at y = 765.
# Gap = 765 - 720 = 45px >= 40px!

# Bottom boxes:
# y = 765 to 1130 (height = 365)
# Bottom margin inside host: 1160 - 1130 = 30px.

# Gap between columns:
# Left column: x = 80 to 770 (w = 690)
# Right column: x = 830 to 1520 (w = 690)
# Gap = 830 - 770 = 60px >= 40px!

print("All gaps verified: >= 40px everywhere!")
