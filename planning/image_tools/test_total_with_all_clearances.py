# Box heights:
h1 = 56 # Shared host
h2 = 210 # Lane 1
h3 = 260 # Lane 2
h4 = 134 # Lane 3
h5 = 134 # Footer
h6 = 56 # Takeaway

# Gaps: 5 gaps of 40px
gaps = 5 * 40 # 200

# Total boxes + gaps:
total_boxes = h1 + h2 + h3 + h4 + h5 + h6 + gaps # 850 + 200 = 1050
print("Total boxes + gaps:", total_boxes)

# Canvas height available for boxes:
# Canvas H = 1200
# Top margin = 40
# Title height (line 1 at 76, line 2 at 120 -> bottom = 128)
# Gap title to box 1 = 40
# Bottom margin = 40
# Available for boxes = 1200 - 128 - 40 - 40 = 992px!
# We have 1050px, which is 58px over 992px!
print("Over by:", total_boxes - 992, "px")
