def wrap_card(name, text, font_size, max_w):
    words = text.split()
    lines = []
    curr = []
    for w in words:
        test = " ".join(curr + [w])
        if len(test) * 0.6 * font_size <= max_w:
            curr.append(w)
        else:
            if curr:
                lines.append(" ".join(curr))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))
    print(f"=== {name} (fs={font_size}, max_w={max_w}) ===")
    for idx, l in enumerate(lines, 1):
        w = len(l) * 0.6 * font_size
        print(f"  Line {idx} ({len(l):2d} ch, {w:5.1f} px): {l}")
    total_h = len(lines) * (font_size + 8)
    print(f"  Lines: {len(lines)}, Text height: {total_h} px")
    return lines

max_w = 600 # with card width 710, text from x+88 to x+688

wrap_card("R1_Q1", "Is there a purpose-built module (package, service, user, file, lineinfile, template, sysctl, systemd, mount, cron)?", 24, max_w)
wrap_card("R1_Module", "use it: idempotent, supports check mode, returns structured results", 24, max_w)
wrap_card("R2_Q2", "Does the target have Python?", 28, max_w)
wrap_card("R2_Raw", "raw: plain SSH command with no module and no Python; bootstraps Python on minimal systems and devices", 24, max_w)
wrap_card("R3_Q3", "Need pipes or redirects?", 28, max_w)
wrap_card("R3_Shell", "shell: passes through /bin/sh; vulnerable to quoting and injection mistakes when variables are untrusted", 24, max_w)
wrap_card("R4_Command", "command: no shell, safest; no pipes, redirects or expansion", 24, max_w)
wrap_card("R4_Injection", "a hostname from a ticket sneaks in a second command after a semicolon", 24, max_w)
wrap_card("R5_Q_script", "Need to run a local script on the target?", 25, max_w)
wrap_card("R5_Script", "script: copies a local script to the target and runs it", 24, max_w)
wrap_card("Guard_Strip", "command and shell are not idempotent: add creates: or removes:, a guard task (a small check that decides whether the risky step should run), or changed_when and failed_when; a shell one-liner always reports changed, cannot be dry-run and hides intent", 24, 1380)
wrap_card("Bottom_Bar", "Prefer modules, and guard what you cannot avoid", 28, 1440)
