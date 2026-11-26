# Test vertical layout
H = 1150
y_start = 220

# Top row stage boxes:
# y = 220 to 400 (height 180)
# Gap to tasks = 40px
# Task 1: y = 440 to 520 (height 80)
# Gap = 30px
# Task 2: y = 550 to 630 (height 80)
# Gap = 30px
# Task 3: y = 660 to 760 (height 100)
# Gap = 30px
# Task 4: y = 790 to 910 (height 120)
# Gap to takeaway bar = 40px
# Takeaway bar: y = 980 to 1060 (height 80)
# Bottom margin = 1150 - 1060 = 90px >= 40px!

print("Vertical budget:")
print(f"Top row: y=220..400")
print(f"Task 1:  y=440..520")
print(f"Task 2:  y=550..630")
print(f"Task 3:  y=660..760")
print(f"Task 4:  y=790..910")
print(f"Takeaway: y=980..1060")
print(f"Bottom margin: {H - 1060}px")
