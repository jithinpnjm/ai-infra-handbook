# Let's test every line in Candidate SVG

def check_line(text, fs, font_type, max_w):
    multiplier = 0.62 if font_type == "mono" else 0.6
    w = len(text) * fs * multiplier
    fits = w <= max_w
    pad = max_w - w
    print(f"[{'OK' if fits else 'OVERFLOW'}] w={w:.1f}, avail={max_w:.1f}, pad={pad:.1f} | '{text}'")
    assert fits, f"Line overflow: '{text}' w={w} > {max_w}"

# Col 1 cards: width 700 (x=60..760). Available for text starting at x=202 is 760 - 202 - 16 = 542.
# Available for text starting at x=76 is 760 - 76 - 16 = 668.
print("=== Ladder 1 Card 1 ===")
check_line("ANSIBLE_CONFIG ", 24, "mono", 542)
check_line("environment variable", 24, "sans", 542)

print("\n=== Ladder 1 Card 2 ===")
check_line("./ansible.cfg ", 24, "mono", 542)
check_line("in the current directory ", 24, "sans", 542)
check_line("(honoured only if it is not world-writable: ", 24, "sans", 668)
check_line("a folder any user can change ", 24, "sans", 668)
check_line("cannot be trusted)", 24, "sans", 668)

print("\n=== Ladder 1 Card 3 ===")
check_line("~/.ansible.cfg", 24, "mono", 542)

print("\n=== Ladder 1 Card 4 ===")
check_line("/etc/ansible/ansible.cfg", 24, "mono", 542)

# Col 2 cards: width 700 (x=840..1540). Available for text starting at x=984 is 1540 - 984 - 16 = 540.
print("\n=== Ladder 2 Cards ===")
check_line("command-line flags", 28, "sans", 540)
check_line("environment variables", 28, "sans", 540)
check_line("config file", 28, "sans", 540)
check_line("defaults", 28, "sans", 540)

# Strips: width 1520 (x=40..1560). Available for text starting at x=136 is 1560 - 136 - 16 = 1408.
print("\n=== Commands Strip ===")
check_line("ansible-config dump --only-changed shows only what you changed; ", 24, "mono", 1408)
check_line("ansible-config list shows every setting with its default; ", 24, "mono", 1408)
check_line("ansible --version shows the config file in use", 24, "mono", 1408)

print("\n=== Surprise Story ===")
check_line("an engineer runs Ansible from a folder they did not expect, ", 24, "sans", 1408)
check_line("and the tool quietly picks up a different config file", 24, "sans", 1408)

print("\n=== Rules Strip ===")
check_line("keep a project-level ansible.cfg in the repo root; ", 24, "mono", 1408)
check_line("keep secrets and personal paths out of it because it is committed; ", 24, "sans", 1408)
check_line("editing /etc/ansible changes behaviour between laptops and CI and is invisible to Git", 24, "mono", 1408)

print("\n=== Bottom Bar ===")
check_line("Knowing the search order turns a surprise into a quick check", 24, "sans", 1520 - 32)

print("\nALL LINES FIT WITH PLENTY OF PADDING!")
