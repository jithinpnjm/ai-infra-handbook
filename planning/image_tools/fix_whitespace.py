with open("generate_and_audit.py") as f:
    code = f.read()

# Replace any multi-line text with inline tspans
# For example:
# <text ...>
#   <tspan ...>...</tspan>
# </text>
# Should be:
# <text ...><tspan ...>...</tspan><tspan ...>...</tspan></text>

# Let's inspect how generate_and_audit.py defines svg_content
