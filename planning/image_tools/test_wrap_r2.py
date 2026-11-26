import xml.etree.ElementTree as ET

# Let's verify line wrapping and height for Row 2 left text
text = "Is the CPU the limiter? Single-thread Python launch overhead, torch ops launching tiny kernels"
# Line 1: "Is the CPU the limiter?" (23 chars * 14.4 = 331.2 px)
# Line 2: "Single-thread Python launch overhead," (37 chars * 14.4 = 532.8 px)
# Line 3: "torch ops launching tiny kernels" (32 chars * 14.4 = 460.8 px)

# If max width is 540 px:
# Line 1: "Is the CPU the limiter? Single-thread" (37 chars -> 532.8 px)
# Line 2: "Python launch overhead, torch ops" (33 chars -> 475.2 px)
# Line 3: "launching tiny kernels" (22 chars -> 316.8 px)

print("Line 1:", 37 * 14.4)
print("Line 2:", 33 * 14.4)
print("Line 3:", 22 * 14.4)
