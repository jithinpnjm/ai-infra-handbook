import re

svg = open("test_side_by_side_playwright.svg").read()

# 1. Table 1 & Table 2 headers:
# Change rect y="328" width="685" height="96" to y="326" width="685" height="106"
svg = svg.replace('rect x="70" y="328" width="685" height="96"', 'rect x="70" y="326" width="685" height="106"')
svg = svg.replace('rect x="845" y="328" width="685" height="96"', 'rect x="845" y="326" width="685" height="106"')
# Change text y="366" to y="372"
svg = svg.replace('<text x="160" y="366"', '<text x="160" y="372"')
svg = svg.replace('<text x="935" y="366"', '<text x="935" y="372"')

# 2. T2 Row 1:
# Change rect x="845" y="434" width="685" height="92" to y="438" width="685" height="96"
svg = svg.replace('rect x="845" y="434" width="685" height="92"', 'rect x="845" y="438" width="685" height="96"')
# Change text y="471" to y="474"
svg = svg.replace('<text x="865" y="471"', '<text x="865" y="474"')

# Adjust T2 rows vertical positions:
# Row 1: 438..534 (h=96)
# Row 2: 540..624 (h=84)
svg = svg.replace('rect x="845" y="534" width="685" height="84"', 'rect x="845" y="540" width="685" height="84"')
svg = svg.replace('<text x="865" y="574"', '<text x="865" y="578"')
svg = svg.replace('rect x="1275" y="563"', 'rect x="1275" y="567"')
svg = svg.replace('rect x="1460" y="563"', 'rect x="1460" y="567"')

# Row 3: 630..714 (h=84)
svg = svg.replace('rect x="845" y="626" width="685" height="84"', 'rect x="845" y="630" width="685" height="84"')
svg = svg.replace('<text x="865" y="666"', '<text x="865" y="670"')
svg = svg.replace('rect x="1275" y="655"', 'rect x="1275" y="659"')
svg = svg.replace('rect x="1472" y="655"', 'rect x="1472" y="659"')

# Row 4: 720..804 (h=84)
svg = svg.replace('rect x="845" y="718" width="685" height="84"', 'rect x="845" y="720" width="685" height="84"')
svg = svg.replace('<text x="865" y="758"', '<text x="865" y="760"')
svg = svg.replace('rect x="1275" y="747"', 'rect x="1275" y="749"')
svg = svg.replace('rect x="1478" y="747"', 'rect x="1478" y="749"')

# Row 5: 810..902 (h=92)
svg = svg.replace('<text x="865" y="851"', '<text x="865" y="851"')

open("test_adjusted.svg", "w").write(svg)
