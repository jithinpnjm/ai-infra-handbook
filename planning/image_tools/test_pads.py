# Test exact box dimensions, line wraps, text clearances, and label matching

import re

# Font estimation factors:
# Sans: 0.60 * size
# Mono: 0.62 * size

def text_width(text, size=24, mono=False):
    factor = 0.62 if mono else 0.60
    return len(text) * size * factor

# ==================== LABELS ====================
title = "From a failed unit message or status code to the layer that broke"

left_header = "Message from systemctl or the journal"
left_pairs = [
    # (msg, msg_lines, cause, cause_lines)
    (
        "Failed to start X: Unit X not found",
        ["Failed to start X:", "Unit X not found"],
        "wrong name, path or alias; daemon-reload may fix it",
        ["wrong name, path or", "alias; daemon-reload", "may fix it"]
    ),
    (
        "Job for X failed because the control process exited with error code",
        ["Job for X failed", "because the control", "process exited with", "error code"],
        "read journalctl -xeu X",
        ["read journalctl -xeu X"]
    ),
    (
        "start request repeated too quickly",
        ["start request", "repeated too quickly"],
        "start limit hit: reset-failed, fix the cause, lengthen RestartSec",
        ["start limit hit:", "reset-failed, fix the", "cause, lengthen", "RestartSec"]
    ),
    (
        "Dependency failed for X",
        ["Dependency failed", "for X"],
        "a Requires dependency failed",
        ["a Requires dependency", "failed"]
    ),
    (
        "Unit is masked",
        ["Unit is masked"],
        "the unit cannot be started at all",
        ["the unit cannot be", "started at all"]
    )
]

right_header = "status= code"
right_pairs = [
    (
        "203/EXEC",
        ["203/EXEC"],
        "ExecStart binary cannot run: path, permissions, a noexec mount, wrong architecture, or a bad shebang",
        [
            "ExecStart binary cannot run:",
            "path, permissions, a noexec",
            "mount, wrong architecture,",
            "or a bad shebang"
        ]
    ),
    (
        "200/CHDIR",
        ["200/CHDIR"],
        "bad WorkingDirectory=",
        ["bad WorkingDirectory="]
    ),
    (
        "217/USER",
        ["217/USER"],
        "bad User=",
        ["bad User="]
    ),
    (
        "226/NAMESPACE",
        ["226/NAMESPACE"],
        "sandbox mount problem",
        ["sandbox mount problem"]
    ),
    (
        "1/FAILURE",
        ["1/FAILURE"],
        "the program's own exit",
        ["the program's own exit"]
    ),
    (
        "signal=KILL or code=killed",
        ["signal=KILL or", "code=killed"],
        "killed by the OOM killer or a timeout",
        ["killed by the OOM killer", "or a timeout"]
    ),
    (
        "Result: timeout",
        ["Result: timeout"],
        "unit ran past its time limit",
        ["unit ran past its time limit"]
    )
]

commands = [
    "systemctl status",
    "journalctl -u NAME -b",
    "systemctl cat",
    "systemd-analyze verify FILE"
]

takeaway = "Start with the status code, then read the journal for that unit"

# Check left column pairs in boxes:
# Left msg box: w = 325
# Left cause box: w = 360
print("=== CHECKING LEFT COLUMN TEXT PADDING ===")
for msg, msg_lines, cause, cause_lines in left_pairs:
    assert " ".join(msg_lines) == msg, f"Msg mismatch: '{' '.join(msg_lines)}' vs '{msg}'"
    assert " ".join(cause_lines) == cause, f"Cause mismatch: '{' '.join(cause_lines)}' vs '{cause}'"
    
    print(f"\nMSG: {msg}")
    for l in msg_lines:
        w = text_width(l, 24, False)
        pad = (325 - w) / 2
        print(f"  Line: '{l}' (w={w:.1f}px, pad={pad:.1f}px)")
        assert pad >= 16, f"Padding {pad} < 16 for '{l}' in 325px box"
        
    print(f"CAUSE: {cause}")
    for l in cause_lines:
        w = text_width(l, 24, False)
        pad = (360 - w) / 2
        print(f"  Line: '{l}' (w={w:.1f}px, pad={pad:.1f}px)")
        assert pad >= 16, f"Padding {pad} < 16 for '{l}' in 360px box"

print("\n=== CHECKING RIGHT COLUMN TEXT PADDING ===")
# Right code box: w = 260
# Right cause box: w = 440
for code, code_lines, cause, cause_lines in right_pairs:
    assert " ".join(code_lines) == code, f"Code mismatch: '{' '.join(code_lines)}' vs '{code}'"
    assert " ".join(cause_lines) == cause, f"Cause mismatch: '{' '.join(cause_lines)}' vs '{cause}'"
    
    print(f"\nCODE: {code}")
    for l in code_lines:
        w = text_width(l, 24, True) # monospace for code
        pad = (260 - w) / 2
        print(f"  Line: '{l}' (w={w:.1f}px, pad={pad:.1f}px)")
        assert pad >= 16, f"Padding {pad} < 16 for '{l}' in 260px box"
        
    print(f"CAUSE: {cause}")
    for l in cause_lines:
        w = text_width(l, 24, False)
        pad = (440 - w) / 2
        print(f"  Line: '{l}' (w={w:.1f}px, pad={pad:.1f}px)")
        assert pad >= 16, f"Padding {pad} < 16 for '{l}' in 440px box"

print("\nALL HORIZONTAL TEXT PADDINGS >= 16px! (PASS)")
