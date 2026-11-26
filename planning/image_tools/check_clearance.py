# Let's inspect the clearances for arrow labels and lines:

# 1. SSH 22:
# line from (260, 515) to (370, 515).
# text at x=315, y=490.
# y difference: 515 - 490 = 25px. Text baseline is 25px above line, so text bottom is ~15-20px above line. No touching!

# 2. HTTPS 443:
# path: M 150 430 V 210 H 450
# horizontal segment is at y=210, from x=150 to x=450.
# text at x=300, y=190.
# y difference: 210 - 190 = 20px above line. No touching!

# 3. bulk data:
# path: M 150 600 V 710 H 320 V 800
# horizontal segment is at y=710, from x=150 to x=320.
# text at x=235, y=690.
# y difference: 710 - 690 = 20px above line. No touching!

# 4. reverse proxy to interactive app:
# path: M 870 210 H 1445 V 430
# horizontal segment is at y=210, from x=870 to x=1445.
# text at x=1157, y=188.
# y difference: 210 - 188 = 22px above line. No touching!

# Check arrow end points:
# Node B: translate(370, 430), rect width 230, height 170.
# Left edge of B is x=370.
# Arrow from U: ends at x=370, y=515.
# Exact match!

# Node P: translate(450, 130), rect width 420, height 150.
# Left edge of P is x=450.
# Arrow from U: ends at x=450, y=210.
# Exact match!

# Node L: translate(690, 430), rect width 230, height 170.
# Left edge of L is x=690.
# Arrow from B: ends at x=690, y=515.
# Exact match!
# Top edge of L is y=430.
# Arrow from P: line x1="785" y1="280" x2="785" y2="430".
# Top of L is at y=430, x=785 is inside L [690..920].
# Exact match!

# Node S: translate(1020, 430), rect width 230, height 170.
# Left edge of S is x=1020.
# Arrow from L: line x1="920" y1="515" x2="1020" y2="515".
# Right edge of L is 690 + 230 = 920. Left edge of S is 1020.
# Arrow from (920, 515) to (1020, 515).
# Exact match!

# Node C: translate(1330, 430), rect width 230, height 170.
# Left edge of C is x=1330.
# Right edge of S is 1020 + 230 = 1250.
# Arrow from S: line x1="1250" y1="515" x2="1330" y2="515".
# Exact match!
# Top edge of C is y=430. Center is 1330 + 115 = 1445.
# Orange arrow from P: path ends at (1445, 430).
# Exact match!

# Node D: translate(150, 800), rect width 440, height 175.
# Top edge of D is y=800. x=320 is inside D [150..590].
# Arrow from U ends at (320, 800).
# Exact match!

# Node ST: translate(710, 800), rect width 540, height 175.
# D to ST: D right edge is 150 + 440 = 590. ST left edge is 710.
# Line from (590, 887) to (710, 887).
# Exact match!
# L to ST: L bottom is 430 + 170 = 600. ST top is 800.
# Line from (845, 600) to (845, 800).
# Both x=845 are inside L [690..920] and ST [710..1250].
# Exact match!
# C to ST: C bottom is 600. Center x=1445.
# Path: M 1445 600 V 887 H 1250.
# ST right edge is 710 + 540 = 1250!
# Path enters ST right edge at (1250, 887).
# Exact match!

print("All connection endpoints match box boundaries exactly!")
