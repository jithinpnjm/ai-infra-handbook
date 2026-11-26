with open("test_output_candidate.svg") as f:
    svg = f.read()

# Make Block 1 dashed rect wrap [X for X in range(5)]:
# starts at x="260", width="326"
svg = svg.replace(
    '<rect x="260" y="162" width="430" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>',
    '<rect x="260" y="162" width="326" height="36" rx="6" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 3"/>'
)

with open("test_output_candidate.svg", "w") as f:
    f.write(svg)

print("Final SVG ready in test_output_candidate.svg")
