# Let's test with cy = y_box + 40:
# Lane 1: y=264, h=186
# Circle cx=76, cy=304, r=24.
# Circle top = 304 - 24 = 280 (pad from 264 = 16px!).
# Circle bot = 304 + 24 = 328.
# Title baseline = 312. (Title cap = 312 - 22.5 = 289.5, desc = 312 + 6 = 318).
# Next lines:
# Line 1: baseline = 336
# Line 2: baseline = 360
# Line 3: baseline = 384
# Line 4: baseline = 408
# Line 5: baseline = 430.
# Desc = 430 + 4.8 = 434.8.
# Box bot = 450. Pad bot = 450 - 434.8 = 15.2px.
# If Lane 1 is h=188 (y=264..452): pad bot = 17.2px!
# Where can we get 2px? Gap 5 was 44px, make it 42px!
print("Circle centering fits perfectly!")
