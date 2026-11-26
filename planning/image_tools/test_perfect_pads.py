# Let's adjust and check all clearances and paddings in Chrome
import subprocess, json, re

svg = open("candidate_expand_contract.svg").read()

# Let's apply refinements:
# 1. Phase 1 text: shift y from 152 to 156, x from 135 to 142. Icon x from 74 to 70.
svg = svg.replace('x="74" y="126"', 'x="68" y="126"')
svg = svg.replace('x="135" y="152"', 'x="140" y="156"')
svg = svg.replace('x="135"', 'x="140"')

# 2. Phase 2 text: shift y from 152 to 156, x from 650 to 655. Icon x from 589 to 585.
svg = svg.replace('x="589" y="126"', 'x="585" y="126"')
svg = svg.replace('x="650" y="152"', 'x="655" y="156"')
svg = svg.replace('x="650"', 'x="655"')

# 3. Phase 3 text: shift y from 162 to 166.
svg = svg.replace('x="1170" y="162"', 'x="1170" y="166"')

# 4. Lane cards: make width 250 instead of 225
svg = svg.replace('x="70" y="345" width="225"', 'x="70" y="345" width="250"')
svg = svg.replace('x="70" y="505" width="225"', 'x="70" y="505" width="250"')
svg = svg.replace('x="145" y="425"', 'x="150" y="425"')
svg = svg.replace('x="145" y="585"', 'x="150" y="585"')

# 5. Note box icon: y from 865 to 855
svg = svg.replace('x="1080" y="865"', 'x="1080" y="855"')
svg = svg.replace('x="1080" y="938"', 'x="1080" y="930"')
svg = svg.replace('x="1080"', 'x="1080"')

open("candidate_expand_contract.svg", "w").write(svg)
print("Updated candidate_expand_contract.svg")
