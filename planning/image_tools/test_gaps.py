# If all gaps are 40px:
# Title: baseline 50, 98 -> text ends at 104.
# Gap 1: 40px -> Lanes top = 144.
# Lane height = 310 -> Lanes bottom = 454.
# Gap 2: 40px -> Fix top = 494.
# Fix height = 144 -> Fix bottom = 638.
# Gap 3: 40px -> Checks top = 678.
# Checks height = 140 -> Checks bottom = 818.
# Gap 4: 40px -> Rules top = 858.
# Rules height = 148 -> Rules bottom = 1006.
# Gap 5: 40px -> Bar top = 1046.
# Bar height = 56 -> Bar bottom = 1102.
# Margin bottom: 1200 - 1102 = 98px (>= 40px)!

print("Gaps check:")
print("Title bottom: 104")
print("Gap Title->Lanes:", 144 - 104)
print("Gap Lanes->Fix:", 494 - 454)
print("Gap Fix->Checks:", 678 - 638)
print("Gap Checks->Rules:", 858 - 818)
print("Gap Rules->Bar:", 1046 - 1006)
print("Bar bottom:", 1102)
print("Margin bottom:", 1200 - 1102)
