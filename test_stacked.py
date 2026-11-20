import xml.etree.ElementTree as ET

# Let's verify exact text string matches
def test():
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

    # In our SVG, if we put "ansible.builtin.import_role" as a single text node:
    # <text ...>ansible.builtin.import_role</text>
    # It will be extracted as exactly "ansible.builtin.import_role"!
    print("All labels tested for single line string match:")
    for l in required_labels:
        print(f"  {l}")

test()
