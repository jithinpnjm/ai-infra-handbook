labels = [
    "Exit codes tell you what happened, from 0 for success to 128 plus N for a signal",
    "0",
    "Success",
    "1",
    "General error. For grep, diff and cmp: no match or files differ, not an error",
    "2",
    "Misuse of a command, or a real error for grep and diff",
    "126",
    "Found but not executable",
    "127",
    "Command not found",
    "128 + N",
    "130 Ctrl-C",
    "137 SIGKILL",
    "143 SIGTERM",
    "255",
    "Status out of range, or ssh connection failure",
    "Read the code, then check which program produced it."
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. '{l}'")
