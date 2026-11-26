# Let's test Row 2 layout options
left_text = "Is the CPU the limiter? Single-thread Python launch overhead, torch ops launching tiny kernels"
fix_text = "fix: CUDA graphs or compile"

# If Row 2 text is 2 lines:
# Line 1: Is the CPU the limiter? Single-thread Python launch overhead,
# Line 2: torch ops launching tiny kernels
# Width of line 1: 60 chars * 14.4 = 864 px! That leaves only 76 px for the fix pill.

# What if left_text has 3 lines?
# In height 108 px:
# 3 lines of 24px: line height 28px -> 3 * 28 = 84 px. Fits in 108 px with 12px padding!
# But wait, 16px padding is required!
# "Every text line must fit inside its box with at least 16 px padding."
# 108 - 2 * 16 = 76 px vertical budget!
# 3 lines need at least 24 * 3 = 72 px, with leading 28 px it's 24 + 28 + 28 = 80 px > 76 px!
# So 3 lines might violate the 16px vertical padding if box height is 108px!

# BUT WAIT! Can Row 2 box be taller, or can all row boxes have different heights, OR can the left area be wider?
print("Let's analyze row heights and widths!")
