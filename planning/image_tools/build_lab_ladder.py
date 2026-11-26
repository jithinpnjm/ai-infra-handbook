import xml.etree.ElementTree as ET
import re

# Let's write the generator script for 3 columns:
# Col 1: Group 1 (steps 1-2)
# Col 2: Group 2 (steps 3-7, orange)
# Col 3: Group 3 (steps 8-12)

# First, let's carefully define the text lines for each step such that:
# 1. Concatenating all lines with space equals the exact source label!
# 2. Every single line fits in the available card width (448px) with padding >= 16px!
# 3. Every line is >= 24px font size!
# 4. Step titles are >= 30px bold!
# 5. Total text height fits in the card height with vertical padding >= 16px!

# Let's test this in Python!
