# Row 1 trap:
# 525px box width
# Max text width = 525 - 32 = 493px
# If 4 lines:
lines_4 = [
    "float precision, large integers, NaN,", # len 37, sans: 37*14.4 = 532px > 493px!
]
# What if:
lines_4_b = [
    "float precision, large integers,", # 32 chars: 32*14.4 = 460.8px < 493px (OK!)
    "NaN, duplicate keys; JSON Lines for", # 35 chars: 35*14.4 = 504px > 493px (FAIL!)
]
# So 5 lines is needed for Row 1 trap to guarantee every line <= 493px!
print("Row 1 trap needs 5 lines.")
