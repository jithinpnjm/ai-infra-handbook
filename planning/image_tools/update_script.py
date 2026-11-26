with open("generate_final_svg.py") as f:
    code = f.read()

# Update bottom bar
code = code.replace(
'''# Bottom Bar
bottom_y = cur_y + 10 # 1096 + 10 = 1106
bottom_h = 74
lines.append('  <!-- Bottom Takeaway Bar (Highlighted in Orange) -->')
lines.append('  <g id="bottom-bar">')
lines.append(f'    <rect x="40" y="{bottom_y}" width="1520" height="{bottom_h}" rx="8" fill="#fef5ed" stroke="#db8129" stroke-width="2.5"/>')
lines.append(f'    <rect x="40" y="{bottom_y}" width="12" height="{bottom_h}" rx="4" fill="#db8129"/>')
# Icon on bottom bar: orange badge with white checkmark
lines.append(f'    <g transform="translate(64, {bottom_y + 19})">')
lines.append('      <circle cx="18" cy="18" r="16" fill="#db8129"/>')
lines.append('      <polyline points="10,18 16,24 26,12" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
lines.append('    </g>')
# Text in 2 lines inside bottom bar
lines.append(f'    <text x="116" y="{bottom_y + 32}" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
lines.append(f'      <tspan x="116" dy="0">{bottom_lines[0]}</tspan>')
lines.append(f'      <tspan x="116" dy="28">{bottom_lines[1]}</tspan>')
lines.append('    </text>')
lines.append('  </g>')''',
'''# Bottom Bar
bottom_y = 1100
bottom_h = 84
lines.append('  <!-- Bottom Takeaway Bar (Highlighted in Orange) -->')
lines.append('  <g id="bottom-bar">')
lines.append(f'    <rect x="40" y="{bottom_y}" width="1520" height="{bottom_h}" rx="8" fill="#fef5ed" stroke="#db8129" stroke-width="2.5"/>')
lines.append(f'    <rect x="40" y="{bottom_y}" width="12" height="{bottom_h}" rx="4" fill="#db8129"/>')
# Icon on bottom bar: orange badge with white checkmark
lines.append(f'    <g transform="translate(64, {bottom_y + 24})">')
lines.append('      <circle cx="18" cy="18" r="16" fill="#db8129"/>')
lines.append('      <polyline points="10,18 16,24 26,12" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
lines.append('    </g>')
# Text in 2 lines inside bottom bar
lines.append(f'    <text x="118" y="{bottom_y + 35}" font-family="system-ui, -apple-system, sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
lines.append(f'      <tspan x="118" dy="0">{bottom_lines[0]}</tspan>')
lines.append(f'      <tspan x="118" dy="26">{bottom_lines[1]}</tspan>')
lines.append('    </text>')
lines.append('  </g>')'''
)

with open("generate_final_svg.py", "w") as f:
    f.write(code)

import subprocess
subprocess.run(["python3", "generate_final_svg.py"], check=True)
subprocess.run(["python3", "test_validate.py"], check=True)
