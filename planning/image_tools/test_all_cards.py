import sys

# All cards definition:
# Card dimensions:
# Width = 715 px
# Height = 125 px
# Left cards: x = 40 to 755
# Right cards: x = 845 to 1560
# Icon at: x = card_x + 18, y = card_y + (125 - 56)/2 = card_y + 34.5 (width=56, height=56)
# Text starts at x = card_x + 88.
# Available width = 715 - 88 - 20 = 607 px.

cards = [
    {
        "id": "R1_Q1",
        "name": "Q1 (Module Question)",
        "x": 40, "y": 115, "w": 715, "h": 125,
        "lines": [
            ("Is there a purpose-built module", 30, True),
            ("(package, service, user, file, lineinfile,", 24, False),
            ("template, sysctl, systemd, mount, cron)?", 24, False)
        ]
    },
    {
        "id": "R1_Module",
        "name": "Module (use it)",
        "x": 845, "y": 115, "w": 715, "h": 125,
        "lines": [
            ("use it: idempotent,", 30, True),
            ("supports check mode,", 25, False),
            ("returns structured results", 25, False)
        ]
    },
    {
        "id": "R2_Q2",
        "name": "Q2 (Python Question)",
        "x": 40, "y": 280, "w": 715, "h": 125,
        "lines": [
            ("Does the target have Python?", 30, True)
        ]
    },
    {
        "id": "R2_Raw",
        "name": "Raw",
        "x": 845, "y": 280, "w": 715, "h": 125,
        "lines": [
            ("raw: plain SSH command", 30, True),
            ("with no module and no Python; bootstraps", 24, False),
            ("Python on minimal systems and devices", 24, False)
        ]
    },
    {
        "id": "R3_Q3",
        "name": "Q3 (Pipes Question)",
        "x": 40, "y": 445, "w": 715, "h": 125,
        "lines": [
            ("Need pipes or redirects?", 30, True)
        ]
    },
    {
        "id": "R3_Shell",
        "name": "Shell",
        "x": 845, "y": 445, "w": 715, "h": 125,
        "lines": [
            ("shell: passes through /bin/sh;", 30, True),
            ("vulnerable to quoting and injection", 24, False),
            ("mistakes when variables are untrusted", 24, False)
        ]
    },
    {
        "id": "R4_Command",
        "name": "Command",
        "x": 40, "y": 610, "w": 715, "h": 125,
        "lines": [
            ("command: no shell, safest;", 30, True),
            ("no pipes, redirects or expansion", 24, False)
        ]
    },
    {
        "id": "R4_Injection",
        "name": "Injection Example",
        "x": 845, "y": 610, "w": 715, "h": 125,
        "lines": [
            ("a hostname from a ticket sneaks in a", 28, True),
            ("second command after a semicolon", 24, False)
        ]
    },
    {
        "id": "R5_Q_script",
        "name": "Q Script (Another branch Question)",
        "x": 40, "y": 775, "w": 715, "h": 125,
        "lines": [
            ("Need to run a local script", 30, True),
            ("on the target?", 26, False)
        ]
    },
    {
        "id": "R5_Script",
        "name": "Script (Another branch Outcome)",
        "x": 845, "y": 775, "w": 715, "h": 125,
        "lines": [
            ("script: copies a local script", 30, True),
            ("to the target and runs it", 24, False)
        ]
    }
]

# Guard Strip:
guard_strip = {
    "id": "Guard_Strip",
    "x": 40, "y": 940, "w": 1520, "h": 125,
    "lines": [
        ("command and shell are not idempotent: add creates: or removes:, a guard task (a small check", 24, True),
        ("that decides whether the risky step should run), or changed_when and failed_when; a shell", 24, False),
        ("one-liner always reports changed, cannot be dry-run and hides intent", 24, False)
    ]
}

# Bottom Bar:
bottom_bar = {
    "id": "Bottom_Bar",
    "x": 40, "y": 1105, "w": 1520, "h": 55,
    "lines": [
        ("Prefer modules, and guard what you cannot avoid", 28, True)
    ]
}

failed = False

for c in cards:
    print(f"\nChecking Card: {c['name']} ({c['id']})")
    text_x = c['x'] + 88
    max_text_w = c['w'] - 88 - 16
    for idx, (t, fs, b) in enumerate(c['lines']):
        tw = len(t) * 0.6 * fs
        pad_right = c['w'] - (88 + tw)
        ok = pad_right >= 16
        print(f"  Line {idx+1}: '{t}' | fs={fs} | w={tw:.1f}px | pad_r={pad_right:.1f}px [{'OK' if ok else 'FAIL'}]")
        if not ok:
            failed = True
            
print(f"\nChecking Guard Strip:")
max_guard_w = guard_strip['w'] - 88 - 16
for idx, (t, fs, b) in enumerate(guard_strip['lines']):
    tw = len(t) * 0.6 * fs
    pad_right = guard_strip['w'] - (88 + tw)
    ok = pad_right >= 16
    print(f"  Line {idx+1}: '{t}' | fs={fs} | w={tw:.1f}px | pad_r={pad_right:.1f}px [{'OK' if ok else 'FAIL'}]")
    if not ok:
        failed = True

print(f"\nChecking Bottom Bar:")
for idx, (t, fs, b) in enumerate(bottom_bar['lines']):
    tw = len(t) * 0.6 * fs
    pad_left = (bottom_bar['w'] - tw) / 2
    ok = pad_left >= 16
    print(f"  Line {idx+1}: '{t}' | fs={fs} | w={tw:.1f}px | pad_side={pad_left:.1f}px [{'OK' if ok else 'FAIL'}]")
    if not ok:
        failed = True

if failed:
    print("\n--> SOME CHECKS FAILED!")
else:
    print("\n--> ALL CARDS PASSED PADDING AND FIT CHECKS!")
