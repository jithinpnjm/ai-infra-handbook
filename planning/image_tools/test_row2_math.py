# Let's test the horizontal layout of Row 2
# Row 2 box: x = 40 to 1080 (width 1040)
# Icon and number circle: x = 40 to 162
# Text start: x = 180

# Question text:
# Line 1: "Is the CPU the limiter? Single-thread Python launch overhead,"
# Line 2: "torch ops launching tiny kernels"

l1 = "Is the CPU the limiter? Single-thread Python launch overhead,"
l2 = "torch ops launching tiny kernels"
fix = "fix: CUDA graphs or compile"

w_l1 = len(l1) * 14.4
w_l2 = len(l2) * 14.4
w_fix = len(fix) * 14.4

print(f"Line 1 width: {len(l1)} chars = {w_l1:.1f}px. Ends at x = {180 + w_l1:.1f}. Right margin to 1080 = {1080 - (180 + w_l1):.1f}px")
print(f"Line 2 width: {len(l2)} chars = {w_l2:.1f}px. Ends at x = {180 + w_l2:.1f}")

# Fix badge / pill on the right of line 2:
# If fix starts at x = 670:
print(f"Fix text: {len(fix)} chars = {w_fix:.1f}px. If starts at x=670, ends at x = {670 + w_fix:.1f}. Right margin to 1080 = {1080 - (670 + w_fix):.1f}px")
print(f"Gap between Line 2 (x={180+w_l2:.1f}) and Fix (x=670): {670 - (180 + w_l2):.1f}px")
