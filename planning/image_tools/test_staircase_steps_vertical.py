# Let's test the vertical separation of steps and diamonds:
# Canvas usable Y for staircase: y = 290 to 810 (520 px height).
#
# Let's see:
# Can we have:
# Step 1: y = 710..810 (h=100)
# Diamond 1: cy = 665, h=70 -> y = 630..700
# Step 2: y = 520..620 (h=100)
# Diamond 2: cy = 475, h=70 -> y = 440..510
# Step 3: y = 330..430 (h=100)
# Diamond 3: cy = 285 ... wait, that's only 3 steps and 2 diamonds and we already reached y=330!
# Because each step + diamond took (100 + 70 + gaps) = 190 px!
# 190 * 5 = 950 px > 520 px!
print("Cannot separate strictly in Y across all 6 steps within 520px")
