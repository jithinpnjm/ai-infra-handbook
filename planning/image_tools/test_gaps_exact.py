# Let's test the gap geometry:
# 6 boxes of width W_box
# 5 diamonds of width W_dia
# Gaps between box and diamond = G

W_box = 160
# For diamond:
# Text "gates" at 24px is 72px wide.
# Diamond width W_dia:
# If W_dia = 96 px:
# Inside diamond, width at text line is ~76px.
# Can W_dia be 100 px?
W_dia = 100

# Let's see: 6 * 160 = 960 px.
# 5 * 100 = 500 px.
# Total width of 11 elements = 1460 px.
# Canvas width = 1600.
# If they all have gaps G in X:
# 10 * G + 1460 <= 1600
# 10 * G <= 140 -> G <= 14 px.
# That would mean 14px gap.
# BUT wait! Does a diamond have to be separated from the step in X?
# Or can the diamond sit between the steps on the staircase,
# connecting them with clean lines?
print("Exploring connection design")
