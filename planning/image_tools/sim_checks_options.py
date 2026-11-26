# Let us test 4 cards in Checks strip:
# Usable x: 136 to 1540 (width 1404px).
# Option A: 2 columns, 2 rows
# Left col (x=136..680, w=544):
#   Card 1: which python (1 line, 12 chars = 178px)
#   Card 2: python -m pip show x (1 line, 20 chars = 297px)
# Right col (x=700..1540, w=840):
#   Card 3: python -c "import sys; print(sys.prefix, sys.base_prefix)" (they differ inside a venv)
#     Line 1: python -c "import sys; print(sys.prefix, (41 chars = 610px)
#     Line 2: sys.base_prefix)" (they differ inside a venv) (45 chars = 656px)
#   Card 4: python -m site shows sys.path, user site and whether a venv is active
#     Line 1: python -m site shows sys.path, user site (40 chars = 590px)
#     Line 2: and whether a venv is active (28 chars = 403px)

# But wait! If Card 3 has 2 lines and Card 4 has 2 lines,
# Card 3 height = 80px, Card 4 height = 80px.
# Total height = 80 + 10 + 80 = 170px!
# Checks container height = 194px (with 12px top and bottom pad).
# Let us check if we have 194px for Checks container:
# Title: 40..104 (ends 104)
# Gap: 40 -> Lanes: 144..500 (h=356)
# Gap: 40 -> Fix: 540..670 (h=130)
# Gap: 40 -> Checks: 710..904 (h=194)
# Gap: 40 -> Rules: 944..1080 (h=136)
# Gap: 40 -> Bar: 1120..1160 (h=40? wait, bar with 24px text needs h=50..56!)
# If Bar h=50 -> Bar: 1120..1170.
# 1170 > 1160! Outside bottom margin 1200 - 1170 = 30px < 40px!

# So Checks cannot be 194px high if total H is 1200!
print("Checks 194px overflows bottom margin of 1200!")
