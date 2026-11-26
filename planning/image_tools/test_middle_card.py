from test_card_text import check_card

c3_lines = [
    [("iptables degrades", 28, False)],
    [("beyond roughly", 28, False)],
    [("5,000 Services", 28, False)],
    [("or 25,000", 28, False)],
    [("endpoints", 28, False)],
]
# Wait, let us check font sizes:
# If font_size is 26 or 28:
# "iptables degrades" at 26px: 17 * 0.6 * 26 = 265.2 < 292.
# At 28px: 17 * 0.6 * 28 = 285.6 < 292.
check_card("Middle: Threshold Marker", c3_lines, 340, 890, pad=24, icon_h=56, icon_gap=24)

# What if we format it as:
# Line 1: iptables degrades (30px bold) - wait, "iptables degrades" at 30px is 17 * 0.6 * 30 = 306 > 292!
# So 26px or 27px or 28px fits! Or 3 lines:
c3_lines_alt = [
    [("iptables", 30, False)],
    [("degrades beyond", 26, False)],
    [("roughly 5,000", 26, False)],
    [("Services or", 26, False)],
    [("25,000 endpoints", 26, False)],
]
check_card("Middle: Alternative", c3_lines_alt, 340, 890, pad=24, icon_h=56, icon_gap=24)
