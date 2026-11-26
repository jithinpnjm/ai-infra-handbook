# Check clearance:
# Container box: x=60..240, y=520..585
# Arrow: x=150, y=475..520
# Label: x=260..563, y=530..570
# FW box: x=530..960, y=325..475
# Fixes box: x=40..980, y=625..800

print("Clearance check:")
print("Arrow x=150, Container box x=60..240 (arrow ends at top edge of container box y=520)")
print("Label x=260..562.4, y=535, 560")
print("Container box right edge: 240. Label left edge: 260. Gap =", 260 - 240, "px")
print("FW box bottom: 475. Label top: ~515. Gap =", 515 - 475, "px")
print("Label bottom: ~570. Fixes box top: 625. Gap =", 625 - 570, "px")
