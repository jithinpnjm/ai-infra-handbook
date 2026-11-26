def check_card(name, lines_with_sizes, max_w=600):
    print(f"=== {name} (max_w={max_w}) ===")
    total_w = 0
    for idx, (text, size, weight) in enumerate(lines_with_sizes, 1):
        w = len(text) * 0.6 * size
        fits = w <= max_w
        print(f"  L{idx} [{size}px {weight}] ({len(text):2d} ch, {w:5.1f} px): '{text}' [{'OK' if fits else 'FAIL'}]")

# R1_Q1
check_card("R1_Q1", [
    ("Is there a purpose-built module", 30, "bold"),
    ("(package, service, user, file, lineinfile,", 24, "normal"),
    ("template, sysctl, systemd, mount, cron)?", 24, "normal")
])

# R1_Module
check_card("R1_Module", [
    ("use it: idempotent,", 30, "bold"),
    ("supports check mode,", 25, "normal"),
    ("returns structured results", 25, "normal")
])

# R2_Q2
check_card("R2_Q2", [
    ("Does the target have Python?", 30, "bold")
])

# R2_Raw
check_card("R2_Raw", [
    ("raw: plain SSH command", 30, "bold"),
    ("with no module and no Python; bootstraps", 24, "normal"),
    ("Python on minimal systems and devices", 24, "normal")
])

# R3_Q3
check_card("R3_Q3", [
    ("Need pipes or redirects?", 30, "bold")
])

# R3_Shell
check_card("R3_Shell", [
    ("shell: passes through /bin/sh;", 30, "bold"),
    ("vulnerable to quoting and injection", 24, "normal"),
    ("mistakes when variables are untrusted", 24, "normal")
])

# R4_Command
check_card("R4_Command", [
    ("command: no shell, safest;", 30, "bold"),
    ("no pipes, redirects or expansion", 24, "normal")
])

# R4_Injection
check_card("R4_Injection", [
    ("a hostname from a ticket sneaks", 28, "bold"),
    ("in a second command after a semicolon", 24, "normal")
])

# R5_Q_script
check_card("R5_Q_script", [
    ("Need to run a local script", 30, "bold"),
    ("on the target?", 26, "normal")
])

# R5_Script
check_card("R5_Script", [
    ("script: copies a local script", 30, "bold"),
    ("to the target and runs it", 24, "normal")
])
