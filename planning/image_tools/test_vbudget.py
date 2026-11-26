#!/usr/bin/env python3
# Test vertical layout and card heights

# Font size = 24
# line height = 28
# Card padding top = 16, bottom = 16 -> for N lines, height = 32 + (N-1)*28 + 24 = 28 + N*28 or:
# line 1 baseline = y + 16 + 24*0.8 = y + 35.2
# line N baseline = y + 35.2 + (N-1)*28
# bottom of line N = baseline + 24*0.2? (audit_pad_strict uses ttop = cur_y - fs*0.8, tbot = cur_y)
# Let's check audit_pad_strict:
# ttop = cur_y - fs * 0.8
# tbot = cur_y
# pad_t = ttop - rect_y
# pad_b = rect_bottom - tbot
# So:
# cur_y (line 1) - 24 * 0.8 >= rect_y + 16  =>  cur_y (line 1) >= rect_y + 16 + 19.2 = rect_y + 35.2
# rect_bottom - cur_y (line N) >= 16       =>  rect_bottom >= cur_y (line N) + 16

def calc_card_h(n_lines, fs=24, line_h=28):
    # line 1 baseline = rect_y + 36
    # line N baseline = rect_y + 36 + (n_lines - 1) * line_h
    # rect_bottom = line N baseline + 18
    # height = rect_bottom - rect_y = 36 + (n_lines - 1) * line_h + 18 = 54 + (n_lines - 1) * line_h
    # Also icon height is 56. If icon is placed at rect_y + 16, rect_bottom must be >= rect_y + 16 + 56 + 16 = rect_y + 88.
    h_text = 54 + (n_lines - 1) * line_h
    h_icon = 56 + 32 # 88
    return max(h_text, h_icon)

ipv4_lines = [1, 2, 1, 1, 4, 3, 2, 2, 2, 1]
ipv6_lines = [1, 2, 3, 1, 2, 4, 2, 4, 2]

h4 = [calc_card_h(n) for n in ipv4_lines]
h6 = [calc_card_h(n) for n in ipv6_lines]

print("IPv4 card heights:", h4)
print("Total IPv4 card heights:", sum(h4))
print("IPv6 card heights:", h6)
print("Total IPv6 card heights:", sum(h6))
