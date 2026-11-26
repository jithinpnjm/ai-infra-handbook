# Verify bounds and padding for each line

# Left column: x = 50 to 780 (w=730).
# Inner stack boxes: x = 75 to 755 (w=680).
# Card 1: x = 75, y = 112, w = 680, h = 52. Icon from x=95 to 135. Text is centered at x=430.
# Text: cfg["timeout"], len=14. Mono: 14 * 0.62 * 26 = 225.7px.
# Left edge of text: 430 - 225.7/2 = 317. Right edge: 430 + 112.8 = 542.8.
# Box right edge = 755. Icon right edge = 135.
# Padding from icon: 317 - 135 = 182px. Padding from right edge: 755 - 542.8 = 212.2px. OK!

# Layer 1: x = 75, y = 184, w = 680, h = 52. Icon x=95 to 135. Text starts at x=155.
# Text: cli_args, len=8. Mono: 8 * 0.62 * 26 = 129px.
# Right edge: 155 + 129 = 284px < 755 (margin = 471px). Padding from icon: 155 - 135 = 20px >= 16px. OK!

# Layer 2: x = 75, y = 256, w = 680, h = 64. Icon x=95 to 135. Text starts at x=155.
# Text: os.environ (MYOPS_ prefixed, lowercased), len=40. Mono: 40 * 0.62 * 24 = 595.2px.
# Right edge: 155 + 595.2 = 750.2px. Box right edge = 755.
# Margin to box right edge: 755 - 750.2 = 4.8px.
# WAIT! 4.8px is LESS than 16px padding!
print(f"Layer 2 right margin: 755 - (155 + 40*0.62*24) = {755 - (155 + 40*0.62*24):.1f}px")

