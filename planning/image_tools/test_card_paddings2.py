# Let's adjust heights and baseline positions in generate_and_audit.py
with open("generate_and_audit.py", "r") as f:
    code = f.read()

# Replace case rows heights: height="88" -> height="92"
# and dy="32" -> dy="30"
# and y baselines:
code = code.replace('height="88"', 'height="92"')
code = code.replace('dy="32"', 'dy="30"')

# Case a: y="252" -> y="250", arrow y="262"
code = code.replace('y="252"', 'y="250"')
code = code.replace('y="268"', 'y="266"')
code = code.replace('y1="260" x2="840" y2="260"', 'y1="262" x2="840" y2="262"')

# Case b: y="354" -> y="352", arrow y="364"
code = code.replace('y="354"', 'y="352"')
code = code.replace('y="370"', 'y="368"')
code = code.replace('y1="362" x2="840" y2="362"', 'y1="364" x2="840" y2="364"')

# Case c: y="456" -> y="454", arrow y="466"
code = code.replace('y="456"', 'y="454"')
code = code.replace('y="472"', 'y="470"')
code = code.replace('y1="464" x2="840" y2="464"', 'y1="466" x2="840" y2="466"')

# Case d: y="574" -> y="570", y="558" -> y="552", arrow y="568"
code = code.replace('y="574"', 'y="570"')
code = code.replace('y="558"', 'y="552"')
code = code.replace('y1="566" x2="840" y2="566"', 'y1="568" x2="840" y2="568"')

# Case e: y="660" -> y="656", arrow y="670"
code = code.replace('y="660"', 'y="656"')
code = code.replace('y1="668" x2="840" y2="668"', 'y1="670" x2="840" y2="670"')

with open("generate_and_audit.py", "w") as f:
    f.write(code)

