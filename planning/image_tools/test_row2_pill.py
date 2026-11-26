# Test Row 2 with left area width = 1000 px
# Box x = 40 to 1040
# Icon and number: x = 40 to 162
# Available width inside row = 1040 - 180 = 860 px

# fix: CUDA graphs or compile
# len = 27 chars.
# At 24px: 27 * 14.4 = 388.8 px.
# Pill width with 16px padding on left and right = 388.8 + 32 = 420.8 px -> 425 px.
# Remaining width for question text = 860 - 425 - 20 (gap) = 415 px!
# 415 / 14.4 = 28.8 chars per line.
# 94 chars / 28 = 3.3 lines -> 4 lines!

print("Even at 1000px, 1-line pill on the right forces question into 4 lines.")
