with open("make_svg.py", "r") as f:
    code = f.read()

# Replace spaces before punctuation
code = code.replace(
    '<tspan class="text-mono">operator.index(key)</tspan>\n      <tspan class="text-sans">, which calls </tspan>',
    '<tspan class="text-mono">operator.index(key)</tspan><tspan class="text-sans">, which calls </tspan>'
)

code = code.replace(
    '<tspan class="text-mono">v.__dict__[x]</tspan>\n      <tspan class="text-sans">, which shadows </tspan>',
    '<tspan class="text-mono">v.__dict__[x]</tspan><tspan class="text-sans">, which shadows </tspan>'
)

with open("make_svg.py", "w") as f:
    f.write(code)

