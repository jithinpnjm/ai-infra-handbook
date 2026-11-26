from test_inline_flow import wrap_text, items

# Let's test the inline design:
# Each row has width 1520 (x=40 to 1560)
# Icon at x=55, y=center
# Text starts at x=120, width = 1540 - 120 = 1420 px
# At font 24px (14.4 px/char) -> max_chars = 96
# But wait: the title is 30px bold!
# "1 Primary versus data plane:" is 28 chars.
# At 30px bold (18px/char), 28 * 18 = 504px.
# Remaining width on line 1 = 1420 - 504 = 916px!
# 916px / 14.4 = 63 chars of rule on line 1!
# Rule text for Row 1 is 65 chars!
# So line 1 can take almost all of Row 1!
# Let's write an exact simulation of inline layout.
