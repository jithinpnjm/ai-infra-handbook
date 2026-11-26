content = open("test_candidate_cpuset.svg").read()

# Replace col 3 title
old_str = """    <!-- Column 3 Question Title (30px bold, 3 lines) -->
    <text x="1175" y="210" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="1175" dy="0">weight (cpu.weight): </tspan>
      <tspan x="1175" dy="34">how fairly under</tspan>
      <tspan x="1175" dy="34">contention?</tspan>
    </text>"""

new_str = """    <!-- Column 3 Question Title (30px bold, 3 lines) -->
    <text x="1175" y="222" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
      <tspan x="1175" dy="0">weight (cpu.weight): </tspan>
      <tspan x="1175" dy="32">how fairly under</tspan>
      <tspan x="1175" dy="32">contention?</tspan>
    </text>"""

assert old_str in content, "old_str not found!"
content = content.replace(old_str, new_str)
open("test_candidate_cpuset.svg", "w").write(content)
print("Updated Col 3 title successfully!")
