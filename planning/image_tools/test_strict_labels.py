import re

# Prompt content:
prompt_content = """
Title: Choosing command, shell, raw, script or a real module

CONTENT (use exactly these labels, each once, spelled exactly; add nothing else):
A decision ladder. Question 'Is there a purpose-built module (package, service, user, file, lineinfile, template, sysctl, systemd, mount, cron)?' yes (orange) 'use it: idempotent, supports check mode, returns structured results'. no then 'Does the target have Python?' no 'raw: plain SSH command with no module and no Python; bootstraps Python on minimal systems and devices'. yes then 'Need pipes or redirects?' yes 'shell: passes through /bin/sh; vulnerable to quoting and injection mistakes when variables are untrusted'. no 'command: no shell, safest; no pipes, redirects or expansion'. Another branch 'Need to run a local script on the target?' 'script: copies a local script to the target and runs it'. Guard strip 'command and shell are not idempotent: add creates: or removes:, a guard task (a small check that decides whether the risky step should run), or changed_when and failed_when; a shell one-liner always reports changed, cannot be dry-run and hides intent'. Injection example 'a hostname from a ticket sneaks in a second command after a semicolon'. Bottom bar: 'Prefer modules, and guard what you cannot avoid'.
"""

# Quoted strings in prompt:
quoted = re.findall(r"'([^']+)'", prompt_content)
print("Quoted labels in prompt:")
for i, q in enumerate(quoted, 1):
    print(f" {i:2d}. {q}")

# Plus title:
title = "Choosing command, shell, raw, script or a real module"

# Branch labels:
# yes (orange)
# no
# no
# yes
# yes
# no
print("\nBranch decisions in flow:")
print(" 1. yes (orange)")
print(" 2. no")
print(" 3. no")
print(" 4. yes")
print(" 5. yes")
print(" 6. no")
