# Check Lane 2:
# Circle cx=76, cy=y_box+35, r=24 -> right=100, bottom=y_box+59.
# Title 'c1 to the Internet' at x=116, baseline = y_box + 44.
# Line 1 desc at x=116, baseline = y_box + 76:
# l2_l1 = "default route points at the bridge IP 10.10.0.1; the packet enters the host IP stack, passes FORWARD"
# len = 100 chars -> 100 * 24 * 0.6 = 1440.
# 116 + 1440 = 1556 -> 1560 - 1556 = 4px (too tight for 16px pad!).
# Ah! In Lane 2, if line 1 starts at x=116, 1440px + 116px leaves only 4px on the right!
# But wait! Why does circle need to be on the left of title?
# What if circle is at cx=72, cy=y_box+30, r=20?
# Wait! Rule says: "Number circles (r=24, green, white number)"
# Rule explicitly says r=24!
# If r=24, why not put the title row on its OWN vertical line, and ALL body text starts below the title row?!
# Let's check:
# If Title row is at baseline y_box + 42:
# Circle cy = y_box + 38, r=24 -> circle bottom = y_box + 62.
# Then ALL body text starts at baseline y_box + 90!
# At baseline y_box + 90, top of text is y_box + 90 - 18 = y_box + 72!
# y_box + 72 is 10px BELOW circle bottom (y_box + 62)!
# So ALL body text lines start at x=60, completely below the circle!
# Zero overlap with circle horizontally or vertically!
print("All body text starting below circle bottom guarantees zero overlap!")
