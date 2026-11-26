import re

with open("generate_and_audit.py", "r") as f:
    content = f.read()

# Replace formula-3 text tspans
old_f3 = '''    <text font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, monospace" font-size="24" fill="#303a36">
      <tspan x="1160" y="210">hours_to_empty = </tspan>
      <tspan x="1160" y="248">SLO_period_hours / burn_rate</tspan>
    </text>'''

new_f3 = '''    <text font-family="ui-monospace, SFMono-Regular, Menlo, Monaco, monospace" font-size="24" fill="#303a36">
      <tspan x="1160" y="200">hours_to_empty = </tspan>
      <tspan x="1160" y="238">SLO_period_hours / </tspan>
      <tspan x="1160" y="276">burn_rate</tspan>
    </text>'''

assert old_f3 in content, "old_f3 not found!"
content = content.replace(old_f3, new_f3)

with open("generate_and_audit.py", "w") as f:
    f.write(content)

