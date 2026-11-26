import re

svg = open("candidate_pending.svg").read()
# Strip comments
clean_svg = re.sub(r'<!--.*?-->', '', svg, flags=re.S)
# Also clean up empty lines caused by stripped comments
clean_lines = [line for line in clean_svg.splitlines() if line.strip() != '']
clean_svg = "\n".join(clean_lines)

open("candidate_pending.svg", "w").write(clean_svg)
print("Stripped all comments from candidate_pending.svg")
