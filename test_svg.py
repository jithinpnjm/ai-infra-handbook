import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1120" width="1600" height="1120">
  <title>Where roles, import_role and include_role run in a play</title>
  <desc>Visual infographic explaining the execution lifecycle and placement of roles, import_role, and include_role across play sections.</desc>
</svg>"""

required_labels = [
    "Where roles, import_role and include_role run in a play",
    "pre_tasks",
    "roles and tasks",
    "post_tasks",
    "roles:",
    "classic, runs before tasks",
    "ansible.builtin.import_role",
    "static, fixed at parse time",
    "ansible.builtin.include_role",
    "dynamic, decided at runtime",
    "supports loop and tasks_from",
    "Parse time for import_role",
    "Runtime for include_role",
    "Handlers flush between sections.",
    "the one that can run a role after a reboot or a drain step",
    "Use roles: for simple cases, and the other two for mid-task roles."
]

print(f"Total required labels: {len(required_labels)}")
for l in required_labels:
    print(f" - {l}")
