# If Step 5 box is at y5 - 54 to y5 - 4:
y5 = 440
y6 = 488 # dy = 48

b5_top = y5 - 54 # 386
b5_bot = y5 - 4  # 436

b6_top = y6 - 32 # 456
b6_bot = y6 - 4  # 484

print(f"Step 5 box: [{b5_top}..{b5_bot}]")
print(f"Step 6 box: [{b6_top}..{b6_bot}]")
print(f"Gap between Step 5 and Step 6 boxes: {b6_top - b5_bot} px!")
assert b6_top - b5_bot >= 16, "Overlap!"
print("PERFECT CLEARANCE >= 16px between boxes!")
