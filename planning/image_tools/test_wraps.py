#!/usr/bin/env python3

text_wraps = {
    "title": {
        "lines": ["Code, state and the real cloud: reading drift"],
        "fs": 48,
        "mono": False,
        "box_w": 1520,
        "box_h": 70
    },
    "code_corner": {
        "lines": [
            "Code",
            "(what you want)"
        ],
        "fs": [30, 24],
        "mono": False,
        "box_w": 340,
        "box_h": 170
    },
    "state_corner": {
        "lines": [
            "State",
            "(Terraform's notebook",
            "of what it built)"
        ],
        "fs": [30, 24, 24],
        "mono": False,
        "box_w": 400,
        "box_h": 180
    },
    "cloud_corner": {
        "lines": [
            "Cloud",
            "(what really exists)"
        ],
        "fs": [30, 24],
        "mono": False,
        "box_w": 340,
        "box_h": 170
    },
    "edge_plan": {
        "lines": [
            "plan compares code",
            "and state, after refreshing",
            "state from the cloud"
        ],
        "fs": 24,
        "mono": False,
        "box_w": 440,
        "box_h": 140
    },
    "edge_drift": {
        "lines": [
            "drift is the gap between code and reality:",
            "someone scaled a pool from the console",
            "during an incident, the next apply",
            "would undo it"
        ],
        "fs": 24,
        "mono": False,
        "box_w": 680,
        "box_h": 165
    },
    "edge_import": {
        "lines": [
            "import brings an object",
            "created by hand into state",
            "so apply does not collide;",
            "plan only knows",
            "what is in state"
        ],
        "fs": 24,
        "mono": False,
        "box_w": 440,
        "box_h": 180
    },
    "cmd_refresh": {
        "lines": [
            "terraform plan -refresh-only",
            "updates state to match the outside world",
            "without proposing changes to resources"
        ],
        "fs": 24,
        "mono": [True, False, False],
        "box_w": 720,
        "box_h": 140
    },
    "cmd_exitcode": {
        "lines": [
            "terraform plan -detailed-exitcode",
            "returns 0 for no changes, 1 for error,",
            "2 for changes present"
        ],
        "fs": 24,
        "mono": [True, False, False],
        "box_w": 720,
        "box_h": 140
    },
    "scheduled_job": {
        "lines": [
            "exit code 2 opens a ticket without",
            "a human reading the whole plan"
        ],
        "fs": 24,
        "mono": False,
        "box_w": 720,
        "box_h": 115
    },
    "decision": {
        "lines": [
            "if the emergency change was right,",
            "fix the code; if wrong, re-apply;",
            "never leave it"
        ],
        "fs": 24,
        "mono": False,
        "box_w": 720,
        "box_h": 115
    }
}

all_passed = True
for key, data in text_wraps.items():
    lines = data["lines"]
    bw = data["box_w"]
    bh = data["box_h"]
    fs_list = data["fs"] if isinstance(data["fs"], list) else [data["fs"]] * len(lines)
    mono_list = data["mono"] if isinstance(data["mono"], list) else [data["mono"]] * len(lines)

    print(f"\nChecking {key} (box {bw}x{bh}):")
    for i, line in enumerate(lines):
        fs = fs_list[i]
        cf = 0.62 if mono_list[i] else 0.60
        w = len(line) * cf * fs
        pad = (bw - w) / 2
        ok = pad >= 16
        if not ok:
            all_passed = False
        print(f"  Line {i+1}: len={len(line):2d}, w={w:5.1f}px, pad={pad:4.1f}px [{'OK' if ok else 'FAIL'}] '{line}'")

print(f"\nOverall wrapping test: {'PASSED' if all_passed else 'FAILED'}")
