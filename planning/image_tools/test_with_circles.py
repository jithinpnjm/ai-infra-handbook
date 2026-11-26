import re
import xml.etree.ElementTree as ET

with open("test_adjust_paddings.py") as f:
    code = f.read()

# Let's inspect step 1 in test_adjust_paddings.py
print("Current step 1 snippet:")
for line in code.split("\n")[80:110]:
    print(line)
