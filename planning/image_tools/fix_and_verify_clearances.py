import re

svg = open("test_adjusted.svg").read()

# Row 5 adjustment
svg = svg.replace('rect x="845" y="810" width="685" height="92"', 'rect x="845" y="810" width="685" height="102"')
svg = svg.replace('<text x="865" y="851"', '<text x="865" y="848"')
svg = svg.replace('rect x="865" y="868" width="294" height="22"', 'rect x="865" y="874" width="294" height="20"')
svg = svg.replace('rect x="1170" y="868" width="263" height="22"', 'rect x="1170" y="874" width="263" height="20"')

open("test_adjusted.svg", "w").write(svg)
print("Updated test_adjusted.svg")
