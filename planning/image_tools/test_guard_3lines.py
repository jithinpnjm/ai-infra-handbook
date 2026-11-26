guard_text = "command and shell are not idempotent: add creates: or removes:, a guard task (a small check that decides whether the risky step should run), or changed_when and failed_when; a shell one-liner always reports changed, cannot be dry-run and hides intent"

# Width available: x=40 to 1560 (width 1520).
# Icon: x=58..114 (56px). Text starts at x=130.
# Right margin: 1560 - 30 = 1530.
# Available width = 1530 - 130 = 1400 px!

# Char width at fs=24: 14.4 px.
# 1400 / 14.4 = 97 chars per line!

lines3 = [
    "command and shell are not idempotent: add creates: or removes:, a guard task (a small check that decides",
    "whether the risky step should run), or changed_when and failed_when; a shell one-liner always reports",
    "changed, cannot be dry-run and hides intent"
]

for idx, l in enumerate(lines3, 1):
    w = len(l) * 14.4
    print(f"L{idx} ({len(l)} ch, {w:.1f} px / 1400 px): {l}")

recon = " ".join(lines3)
print("Reconstructed matches:", recon == guard_text)
