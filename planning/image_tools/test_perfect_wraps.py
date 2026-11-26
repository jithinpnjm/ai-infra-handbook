"""Test 470px width boxes and exact text wraps."""

bw = 470
bh = 140
rel_x = 84

nodes_config_30 = {
    "EV": {
        "text": [
            ("Event: CR created/", 30, "bold"),
            ("updated/deleted OR", 24, "normal"),
            ("owned object changed", 24, "normal"),
            ("OR periodic resync", 24, "normal")
        ],
        "y_start": 36, "dy": 26
    },
    "RQ": {
        "text": [
            ("Work queue", 30, "bold"),
            ("(namespace/name)", 24, "normal")
        ],
        "y_start": 62, "dy": 34
    },
    "R": {
        "text": [
            ("Reconcile(request)", 30, "bold")
        ],
        "y_start": 78, "dy": 0
    },
    "F": {
        "text": [
            ("Run finalizer", 30, "bold"),
            ("cleanup → remove", 24, "normal"),
            ("finalizer → return", 24, "normal")
        ],
        "y_start": 46, "dy": 30
    },
    "D": {
        "text": [
            ("deletionTimestamp", 30, "bold"),
            ("set?", 30, "bold")
        ],
        "y_start": 62, "dy": 34
    },
    "G": {
        "text": [
            ("Get CR (cache);", 30, "bold"),
            ("if gone → return", 24, "normal")
        ],
        "y_start": 62, "dy": 34
    },
    "FIN": {
        "text": [
            ("Ensure finalizer", 30, "bold"),
            ("present", 30, "bold")
        ],
        "y_start": 62, "dy": 34
    },
    "V": {
        "text": [
            ("Validate / default", 30, "bold"),
            ("(defensive), resolve", 24, "normal"),
            ("references", 24, "normal")
        ],
        "y_start": 46, "dy": 30
    },
    "S": {
        "text": [
            ("Observe actual", 30, "bold"),
            ("state: children status,", 24, "normal"),
            ("external systems", 24, "normal")
        ],
        "y_start": 46, "dy": 30
    },
    "A": {
        "text": [
            ("Create / patch /", 30, "bold"),
            ("delete children (SSA", 24, "normal"),
            ("or CreateOrUpdate),", 24, "normal"),
            ("set ownerRefs", 24, "normal")
        ],
        "y_start": 36, "dy": 26
    },
    "C": {
        "text": [
            ("Compute desired", 30, "bold"),
            ("children from spec", 24, "normal")
        ],
        "y_start": 62, "dy": 34
    },
    "U": {
        "text": [
            ("Update CR status.", 30, "bold"),
            ("conditions,", 24, "normal"),
            ("observedGeneration", 24, "normal"),
            ("(status subresource)", 24, "normal")
        ],
        "y_start": 36, "dy": 26
    },
    "RQR": {
        "text": [
            ("Needs requeue?", 30, "bold")
        ],
        "y_start": 78, "dy": 0
    },
    "END": {
        "text": [
            ("return Result{}", 30, "bold")
        ],
        "y_start": 78, "dy": 0
    }
}

print(f"=== CHECKING 4-SIDED PADDING ON 470x140 BOXES (rel_x={rel_x}) ===")
all_pass = True
for nid, cfg in nodes_config_30.items():
    y_start = cfg["y_start"]
    dy = cfg["dy"]
    lines = cfg["text"]
    
    for i, (line_text, fs, weight) in enumerate(lines):
        tw = len(line_text) * 0.60 * fs
        pad_L = rel_x
        pad_R = bw - (rel_x + tw)
        y_curr = y_start + i * dy
        
        if i == 0:
            box_pad_T = y_curr - fs * 0.75
        if i == len(lines) - 1:
            box_pad_B = bh - y_curr
            
        if pad_R < 16.0:
            print(f"FAIL PAD_R: {nid} line '{line_text}': tw={tw:.1f}, pad_R={pad_R:.1f} < 16.0")
            all_pass = False
            
    if box_pad_T < 16.0:
        print(f"FAIL PAD_T: {nid} top line: pad_T={box_pad_T:.1f} < 16.0")
        all_pass = False
    if box_pad_B < 16.0:
        print(f"FAIL PAD_B: {nid} bottom line: pad_B={box_pad_B:.1f} < 16.0")
        all_pass = False

if all_pass:
    print("PERFECT! ALL 14 NODES MEET ALL PADDING CONSTRAINTS (>= 16.0px) ON ALL FOUR SIDES!")
