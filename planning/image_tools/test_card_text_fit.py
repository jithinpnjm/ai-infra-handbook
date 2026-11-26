# Let's inspect each card's content, icon, and text wrapping.

# Card width: 680 px
# Icon: 56 px wide, placed at x_offset = 24 px from left edge of card.
# Icon bounds: from card_x + 24 to card_x + 80.
# Gap after icon: 20 px.
# Text starts at x = card_x + 104.
# Card right edge = card_x + 680.
# With 20 px right padding, text max_x = card_x + 660.
# Available width for text: 660 - 104 = 556 px!

# Sans-serif width factor: 0.6 * font_size
# At 26 px: char width = 15.6 px -> 556 / 15.6 = 35.6 chars per line.
# At 25 px: char width = 15.0 px -> 556 / 15.0 = 37.0 chars per line.
# At 24 px: char width = 14.4 px -> 556 / 14.4 = 38.6 chars per line.

cards = {
    "R1_Q1": {
        "title": "Is there a purpose-built module",
        "sub": "(package, service, user, file, lineinfile, template, sysctl, systemd, mount, cron)?",
        "full": "Is there a purpose-built module (package, service, user, file, lineinfile, template, sysctl, systemd, mount, cron)?"
    },
    "R1_Module": {
        "title": "use it: idempotent, supports check mode,",
        "sub": "returns structured results",
        "full": "use it: idempotent, supports check mode, returns structured results"
    },
    "R2_Q2": {
        "full": "Does the target have Python?"
    },
    "R2_Raw": {
        "title": "raw: plain SSH command with no module and",
        "sub": "no Python; bootstraps Python on minimal systems and devices",
        "full": "raw: plain SSH command with no module and no Python; bootstraps Python on minimal systems and devices"
    },
    "R3_Q3": {
        "full": "Need pipes or redirects?"
    },
    "R3_Shell": {
        "title": "shell: passes through /bin/sh; vulnerable to",
        "sub": "quoting and injection mistakes when variables are untrusted",
        "full": "shell: passes through /bin/sh; vulnerable to quoting and injection mistakes when variables are untrusted"
    },
    "R4_Command": {
        "title": "command: no shell, safest;",
        "sub": "no pipes, redirects or expansion",
        "full": "command: no shell, safest; no pipes, redirects or expansion"
    },
    "R4_Injection": {
        "title": "a hostname from a ticket sneaks in a",
        "sub": "second command after a semicolon",
        "full": "a hostname from a ticket sneaks in a second command after a semicolon"
    },
    "R5_Q_script": {
        "full": "Need to run a local script on the target?"
    },
    "R5_Script": {
        "title": "script: copies a local script to the target",
        "sub": "and runs it",
        "full": "script: copies a local script to the target and runs it"
    }
}

print("Checking line lengths for each card:")
for k, v in cards.items():
    print(f"--- {k} ---")
    if "title" in v:
        print(f"  Title ({len(v['title'])} chars): {v['title']}")
        print(f"  Sub   ({len(v['sub'])} chars): {v['sub']}")
    else:
        print(f"  Single ({len(v['full'])} chars): {v['full']}")
