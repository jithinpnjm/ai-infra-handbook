with open("test_output_candidate.svg") as f:
    svg = f.read()

# Replace the dashed box in Block 1:
# <rect x="238" y="152" width="234" height="40" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>
# with:
# <rect x="260" y="162" width="430" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>

svg = svg.replace(
    '<rect x="238" y="152" width="234" height="40" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>',
    '<rect x="260" y="162" width="430" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>'
)

with open("test_output_candidate.svg", "w") as f:
    f.write(svg)

print("Updated test_output_candidate.svg")
