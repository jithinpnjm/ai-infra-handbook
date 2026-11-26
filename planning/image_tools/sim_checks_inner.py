# Checks strip: x=40, y=710, width=1520, height=160.
# Icon on the left: x=64, y=762, width=56, height=56.
# Usable width inside strip: x=140 to 1540 (width 1400px).
# Height: 160px.
# We have 4 items:
# 1. "which python" (12 chars)
# 2. "python -m pip show x" (20 chars)
# 3. "python -c \"import sys; print(sys.prefix, sys.base_prefix)\" (they differ inside a venv)" (86 chars)
# 4. "python -m site shows sys.path, user site and whether a venv is active" (69 chars)

# Can we have:
# Row 1: Item 1, Item 2, Item 3?
# Or Left column (Items 1 and 2):
#   Card 1: which python (height 62px, y=722..784)
#   Card 2: python -m pip show x (height 62px, y=796..858)
# Right column:
#   What if Card 3 and Card 4?
#   If Right column has 2 cards: each card height would be 62px.
#   Can Item 3 fit in 62px (1 line or 2 lines)?
#   Let us test 2 lines in 62px:
#   Line 1: baseline = top + 26 (top pad = 26 - 18 = 8px -> FAIL < 16)
#   So 2 lines in 62px fails the 16px padding rule!
#
# BUT WAIT! What if Checks strip does NOT have sub-cards, but is ONE container rect,
# or has 3 or 4 wide rows/cards?
# Let us check: Does Checks strip require individual rects around each command?
# Notice prompt:
# "Checks strip 'which python', 'python -m pip show x', 'python -c \"import sys; print(sys.prefix, sys.base_prefix)\" (they differ inside a venv)', 'python -m site shows sys.path, user site and whether a venv is active'."
# If Checks strip is a container, can each check item have its own rect card, OR does the strip contain them?
# If each check item has its own card, how many cards?
# What if there are 3 columns?
# Col 1 (w=340): Card 1 (which python) and Card 2 (python -m pip show x)
# Wait, why not 4 cards side by side if canvas was wide enough, but item 3 is 86 chars!
# Wait! What if:
# Card 1 (top): width 1380!
# Card 2 (bottom): width 1380!
# Wait, what if:
# Left column (x=140, w=480):
#   Card 1: which python
#   Card 2: python -m pip show x
# But wait, why put them in sub-cards at all?
# Let us check: in candidate_cfg_order.svg, commands-strip had NO sub-cards!
# It just had a single rect for the strip, an icon, and text!
