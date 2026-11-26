import re

content = open("generate_and_audit_capstone.py").read()

# Replace parser_detail and rules_detail strokes with #207448
content = content.replace(
    "<!-- Parser detail (pure layer detail - orange) -->\n  <rect x=\"940\" y=\"476\" width=\"620\" height=\"234\" rx=\"10\" fill=\"#ffffff\" stroke=\"#db8129\" stroke-width=\"2\" />",
    "<!-- Parser detail -->\n  <rect x=\"940\" y=\"476\" width=\"620\" height=\"234\" rx=\"10\" fill=\"#ffffff\" stroke=\"#207448\" stroke-width=\"2\" />"
)
content = content.replace(
    "<!-- Rules detail (pure layer detail - orange) -->\n  <rect x=\"940\" y=\"750\" width=\"620\" height=\"150\" rx=\"10\" fill=\"#ffffff\" stroke=\"#db8129\" stroke-width=\"2\" />",
    "<!-- Rules detail -->\n  <rect x=\"940\" y=\"750\" width=\"620\" height=\"150\" rx=\"10\" fill=\"#ffffff\" stroke=\"#207448\" stroke-width=\"2\" />"
)

# And keep icons green #207448 on parsers and rules, only border of pure layers in orange!
content = content.replace(
    '<g transform="translate(60, 520)" stroke="#db8129"',
    '<g transform="translate(60, 520)" stroke="#207448"'
)
content = content.replace(
    '<g transform="translate(60, 752)" stroke="#db8129"',
    '<g transform="translate(60, 752)" stroke="#207448"'
)
content = content.replace(
    '<tspan x="136" dy="0" font-family="ui-monospace, monospace" font-weight="bold" fill="#db8129">parsers.py: </tspan>',
    '<tspan x="136" dy="0" font-family="ui-monospace, monospace" font-weight="bold" fill="#207448">parsers.py: </tspan>'
)
content = content.replace(
    '<tspan x="136" dy="0" font-family="ui-monospace, monospace" font-weight="bold" fill="#db8129">rules.py: </tspan>',
    '<tspan x="136" dy="0" font-family="ui-monospace, monospace" font-weight="bold" fill="#207448">rules.py: </tspan>'
)

open("generate_and_audit_capstone.py", "w").write(content)
