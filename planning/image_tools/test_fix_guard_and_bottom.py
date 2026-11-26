# 1. Guard strip wrapping
guard_text = "command and shell are not idempotent: add creates: or removes:, a guard task (a small check that decides whether the risky step should run), or changed_when and failed_when; a shell one-liner always reports changed, cannot be dry-run and hides intent"

# We have 1372 px max width.
# If fs=24, 1372 / 14.4 = 95 chars.
# If 4 lines:
lines = [
    ("command and shell are not idempotent:", 30, True),
    ("add creates: or removes:, a guard task (a small check that decides", 24, False),
    ("whether the risky step should run), or changed_when and failed_when;", 24, False),
    ("a shell one-liner always reports changed, cannot be dry-run and hides intent", 24, False)
]

for idx, (t, fs, b) in enumerate(lines, 1):
    w = len(t) * (18 if b else 14.4)
    print(f"Line {idx} ({len(t)} ch, {w:.1f} px / 1372 px): {t}")

# Check full text equality:
reconstructed = " ".join([l[0] for l in lines])
print("Matches full text:", reconstructed == guard_text)
