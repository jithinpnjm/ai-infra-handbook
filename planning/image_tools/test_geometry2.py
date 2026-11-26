# Theme width: 310 (x: 40 to 350)
# Gap: 16 -> Mistake x: 366
# Mistake width: 724 (x: 366 to 1090)
# Gap: 16 -> Fix x: 1106
# Fix width: 454 (x: 1106 to 1560)

# In Theme: text x = 118
# Max Theme width = 350 - 118 = 232px available.
# 'Quiet error' width = 11 * 18 = 198px.
# Padding right = 232 - 198 = 34px. (> 16px!)

# In Mistake: text x = 386
# Max Mistake line width = 676.8px.
# End = 386 + 676.8 = 1062.8px.
# Box right = 1090px.
# Padding right = 1090 - 1062.8 = 27.2px. (> 16px!)

# In Fix: text x = 1126
# Max Fix line width = 302.4px ('timeouts, references,')
# End = 1126 + 302.4 = 1428.4px.
# Box right = 1560px.
# Padding right = 1560 - 1428.4 = 131.6px. (> 16px!)

print("All paddings strictly > 16px!")
