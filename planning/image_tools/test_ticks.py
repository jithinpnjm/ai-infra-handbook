import xml.etree.ElementTree as ET

# Read current candidate
with open("candidate_final.svg") as f:
    svg_code = f.read()

# Add axis lines with ticks
# In Timeline A:
axis_a = '''
      <!-- Time axis line -->
      <line x1="220" y1="574" x2="1430" y2="574" stroke="#db8129" stroke-width="2" stroke-linecap="round"/>
      <line x1="220" y1="568" x2="220" y2="580" stroke="#db8129" stroke-width="2"/>
      <line x1="1200" y1="568" x2="1200" y2="580" stroke="#db8129" stroke-width="2"/>
      <line x1="1430" y1="568" x2="1430" y2="580" stroke="#db8129" stroke-width="2"/>
'''

# In Timeline B:
axis_b = '''
      <!-- Time axis line -->
      <line x1="220" y1="966" x2="1430" y2="966" stroke="#207448" stroke-width="2" stroke-linecap="round"/>
      <line x1="220" y1="960" x2="220" y2="972" stroke="#207448" stroke-width="2"/>
      <line x1="440" y1="960" x2="440" y2="972" stroke="#207448" stroke-width="2"/>
      <line x1="660" y1="960" x2="660" y2="972" stroke="#207448" stroke-width="2"/>
      <line x1="880" y1="960" x2="880" y2="972" stroke="#207448" stroke-width="2"/>
      <line x1="1100" y1="960" x2="1100" y2="972" stroke="#207448" stroke-width="2"/>
      <line x1="1430" y1="960" x2="1430" y2="972" stroke="#207448" stroke-width="2"/>
'''

svg_code = svg_code.replace('</g>\n    </g>\n  </g>\n  \n  <!-- ==================== CARD 3', axis_a + '    </g>\n  </g>\n  \n  <!-- ==================== CARD 3')
svg_code = svg_code.replace('</g>\n    </g>\n  </g>\n  \n  <!-- ==================== CARD 4', axis_b + '    </g>\n  </g>\n  \n  <!-- ==================== CARD 4')

with open("candidate_with_axes.svg", "w") as f:
    f.write(svg_code)

print("Saved candidate_with_axes.svg")
