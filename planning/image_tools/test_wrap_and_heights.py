def check_wrap(name, lines, font_size, max_w=556):
    print(f"=== {name} (fs={font_size}) ===")
    for idx, l in enumerate(lines, 1):
        w = len(l) * 0.6 * font_size
        fits = w <= max_w
        print(f"  Line {idx} ({len(l):2d} ch, {w:5.1f} px / {max_w} px): {l} [{'OK' if fits else 'OVERFLOW'}]")
    line_h = font_size * 1.3
    total_h = len(lines) * line_h
    print(f"  Total text height: {total_h:.1f} px")

# R1_Q1
check_wrap("R1_Q1", [
    "Is there a purpose-built module",
    "(package, service, user, file, lineinfile,",
    "template, sysctl, systemd, mount, cron)?"
], 25)

# R1_Module
check_wrap("R1_Module", [
    "use it: idempotent, supports check mode,",
    "returns structured results"
], 26)

# R2_Q2
check_wrap("R2_Q2", [
    "Does the target have Python?"
], 30)

# R2_Raw
check_wrap("R2_Raw", [
    "raw: plain SSH command with no module",
    "and no Python; bootstraps Python on",
    "minimal systems and devices"
], 25)

# R3_Q3
check_wrap("R3_Q3", [
    "Need pipes or redirects?"
], 30)

# R3_Shell
check_wrap("R3_Shell", [
    "shell: passes through /bin/sh; vulnerable to",
    "quoting and injection mistakes when variables",
    "are untrusted"
], 25)

# R4_Command
check_wrap("R4_Command", [
    "command: no shell, safest;",
    "no pipes, redirects or expansion"
], 26)

# R4_Injection
check_wrap("R4_Injection", [
    "a hostname from a ticket sneaks in a",
    "second command after a semicolon"
], 26)

# R5_Q_script
check_wrap("R5_Q_script", [
    "Need to run a local script on the target?"
], 26)

# R5_Script
check_wrap("R5_Script", [
    "script: copies a local script to the target",
    "and runs it"
], 26)

# Guard strip (max_w = 1380, fs = 24)
check_wrap("Guard Strip", [
    "command and shell are not idempotent: add creates: or removes:, a guard task (a small check that decides whether",
    "the risky step should run), or changed_when and failed_when; a shell one-liner always reports changed,",
    "cannot be dry-run and hides intent"
], 24, max_w=1380)

# Bottom bar (max_w = 1440, fs = 28)
check_wrap("Bottom bar", [
    "Prefer modules, and guard what you cannot avoid"
], 28, max_w=1440)
