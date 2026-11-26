with open("candidate_test.svg") as f:
    text = f.read()

# Replace the inner orange occurrences:
text = text.replace('stroke="#db8129" stroke-width="2" />\n\n    <!-- Task 1 Track', 'stroke="#207448" stroke-width="2" />\n\n    <!-- Task 1 Track')
text = text.replace('fill="#db8129" fill-opacity="0.3" stroke="#db8129" stroke-width="2"', 'fill="#207448" fill-opacity="0.25" stroke="#207448" stroke-width="2"')
text = text.replace('stroke="#db8129" stroke-width="3.5"', 'stroke="#207448" stroke-width="3.5"')
text = text.replace('fill="#db8129" />\n\n    <!-- Explanation Card 1', 'fill="#207448" />\n\n    <!-- Explanation Card 1')

with open("candidate_test.svg", "w") as f:
    f.write(text)

import re
matches = re.findall(r'#db8129', text, re.IGNORECASE)
print(f"New orange count: {len(matches)}")
for line in text.splitlines():
    if '#db8129' in line:
        print("  ", line.strip())
