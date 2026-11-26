import xml.etree.ElementTree as ET

# Column 3 layout adjustments:
# Header: y=130 to 205 (75px)
# Card 1: y=212, h=92 (bottom=304). text y = 212 + 18 + 24 = 254. dy=28 -> y2=282. bot=288. pad_t=18, pad_b=16.
# Card 2: y=312, h=150 (bottom=462). text y = 312 + 18 + 24 = 354. dy=28 -> y2=382, y3=410, y4=438. bot=444. pad_t=18, pad_b=18.
# Card 3: y=470, h=92 (bottom=562). text y = 470 + 18 + 24 = 512. dy=28 -> y2=540. bot=546. pad_t=18, pad_b=16.
# Card 4: y=570, h=92 (bottom=662). text y = 570 + 18 + 24 = 612. dy=28 -> y2=640. bot=646. pad_t=18, pad_b=16.
# Card 5: y=670, h=60 (bottom=730). text y = 670 + 18 + 24 = 712. bot=718. pad_t=18, pad_b=12 -> let's make h=66 (bottom=736). pad_b = 736 - 718 = 18.
# Column 3 container: y=130 to 750 (h=620). Bottom pad = 750 - 736 = 14 -> make h=625 (bottom=755, pad=19).

# Definitions strip:
# y=865, h=100 (bottom=965).
# text y=907. Line 1: top=883, pad_t=883-865=18. Line 2: y=939, bot=945, pad_b=965-945=20.

print("Updating geometry...")
