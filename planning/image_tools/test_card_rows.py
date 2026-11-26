# Card is at y=278 to y=848, height=570.
# Card padding top and bottom: 15px.
# Usable vertical space: 570 - 30 = 540px.

# 10 rows:
# Row 1: Subject (1 line, height 40)
# Row 2: Issuer (1 line, height 40)
# Row 3: Validity (2 lines, height 58)
# Row 4: Public key (1 line, height 36)
# Row 5: SAN (3 lines or 4 lines, height 88)
# Row 6: Key usage... (2 lines, height 58)
# Row 7: Basic constraints (1 line, height 40)
# Row 8: Authority... (1 line, height 40)
# Row 9: CRL... (1 line, height 40)
# Row 10: Issuer's signature (1 line, height 40)

row_heights = [40, 40, 58, 36, 88, 58, 40, 40, 40, 40]
print("Sum of heights:", sum(row_heights))
gaps = 9 * 6 # 9 gaps of 6px
print("Sum with gaps:", sum(row_heights) + gaps)
print("Remaining padding:", 570 - (sum(row_heights) + gaps))
