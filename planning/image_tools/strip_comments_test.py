import re
import xml.etree.ElementTree as ET

svg = open("final_pinned_budget.svg").read()
# Clean any comments if preferred, or leave them clean
clean_svg = re.sub(r'<!--.*?-->\n?', '', svg, flags=re.S)
ET.fromstring(clean_svg) # test valid XML
open("final_clean_pinned_budget.svg", "w").write(clean_svg)
print("Valid XML!")
