# Let's calculate:
# Title: y = 35..115 (h = 80)
# Gap = 30
# Sec 1: y = 140..290 (h = 150)
# Gap = 40
# Sec 2: y = 330..720 (h = 390)
# Gap = 40
# Sec 3: y = 760..1040 (h = 280)
# Gap = 40
# Sec 4: y = 1080..1150 (h = 70)
# Bottom margin: 1200 - 1150 = 50 >= 40!

print("Sec 1:", 140, 290, "h=", 290-140)
print("Gap 1-2:", 330 - 290)
print("Sec 2:", 330, 720, "h=", 720-330)
print("Gap 2-3:", 760 - 720)
print("Sec 3:", 760, 1040, "h=", 1040-760)
print("Gap 3-4:", 1080 - 1040)
print("Sec 4:", 1080, 1150, "h=", 1150-1080)
print("Bottom margin:", 1200 - 1150)
