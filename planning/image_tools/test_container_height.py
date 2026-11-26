# Let's test the container structure:
# Inside Host container:
# Shared nodes: h = 56
# Gap: 15
# Lane 1: h = 210
# Gap: 15
# Lane 2: h = 260
# Gap: 15
# Lane 3: h = 134
# Host container inner padding top = 16, bottom = 16.
# Total Host container height = 16 + 56 + 15 + 210 + 15 + 260 + 15 + 134 + 16 = 722px!

# Top-level vertical stack:
# Canvas H = 1200.
# Title top = 40. Lines at 74 and 116. Bottom = 124.
# Gap to Host: 40px -> Host starts at 164.
# Host container: 164 to 164 + 722 = 886.
# Gap to Footer: 40px -> Footer starts at 926.
# Footer box: h = 134 -> 926 to 1060.
# Gap to Takeaway: 40px -> Takeaway starts at 1100.
# Takeaway bar: h = 56 -> 1100 to 1156.
# Bottom margin = 1200 - 1156 = 44px!

print("Host container height:", 722)
print("Title: 40..124")
print("Gap: 40")
print("Host container: 164..886")
print("Gap: 40")
print("Footer box: 926..1060")
print("Gap: 40")
print("Takeaway bar: 1100..1156")
print("Bottom margin: 44px (>= 40px)")
assert 1200 - 1156 >= 40
