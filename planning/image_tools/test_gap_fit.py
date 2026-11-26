from sim_layout import check_wrap

# Gap width = 350px (x=450 to 800)
line1 = "published port 8080"
line2 = "answers from anywhere"

w1 = len(line1) * 24 * 0.6
w2 = len(line2) * 24 * 0.6

print(f"Line 1: '{line1}' width = {w1:.1f}px (fits in 350px? {w1 < 350})")
print(f"Line 2: '{line2}' width = {w2:.1f}px (fits in 350px? {w2 < 350})")
