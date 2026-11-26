import re

def char_width(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * fs * factor

labels = [
    "Where a secret can leak in Terraform",
    "Secret passed to a resource: Terraform must know the value to manage the resource, and whatever it knows it may write down",
    "state file is plain text unless the provider protects it",
    "state bucket: private, encrypted at rest, access controlled; protect it as if it held every password",
    "generated credentials end up in state; convenient because Terraform can read the credential back next run, and the same convenience makes the state a target",
    "write-only arguments in a sensitive object",
    "ephemeral variables declared with ephemeral = true",
    "ephemeral resources",
    "a saved plan file holds the full configuration and may hold sensitive values: treat it as sensitive",
    "say what the state holds, who can read it and what you would change; do not claim the older pattern is safe",
    "prefer write-only or ephemeral secrets"
]

print("Checking line wraps:")
for l in labels:
    print(f"\n--- '{l}' ---")
    words = l.split()
    print("Word count:", len(words))
