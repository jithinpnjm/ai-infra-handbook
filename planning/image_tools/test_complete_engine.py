import re

# 9 Participants:
# Row 1: U, S, R, V, X
# Row 2: A, K, C, D

centers = {
    "U": 150.0,
    "A": 312.5,
    "S": 475.0,
    "K": 637.5,
    "R": 800.0,
    "C": 962.5,
    "V": 1125.0,
    "D": 1287.5,
    "X": 1450.0
}

# Row 1 headers: y = 58 to 158 (h = 100)
# Row 2 headers: y = 168 to 268 (h = 100)

headers = [
    # Row 1
    {"id": "U", "row": 1, "cx": 150.0, "lines": ["User /", "controller"], "icon": "window"},
    {"id": "S", "row": 1, "cx": 475.0, "lines": ["Scheduler"], "icon": "clock"},
    {"id": "R", "row": 1, "cx": 800.0, "lines": ["containerd", "(CRI)"], "icon": "box"},
    {"id": "V", "row": 1, "cx": 1125.0, "lines": ["CSI node", "plugin"], "icon": "cylinder"},
    {"id": "X", "row": 1, "cx": 1450.0, "lines": ["runc /", "kernel"], "icon": "terminal"},
    # Row 2
    {"id": "A", "row": 2, "cx": 312.5, "lines": ["API server", "(+etcd)"], "icon": "lock"},
    {"id": "K", "row": 2, "cx": 637.5, "lines": ["Kubelet"], "icon": "gear"},
    {"id": "C", "row": 2, "cx": 962.5, "lines": ["CNI plugin"], "icon": "network"},
    {"id": "D", "row": 2, "cx": 1287.5, "lines": ["Device plugin"], "icon": "chip"}
]

for h in headers:
    by = 58 if h["row"] == 1 else 168
    bx = h["cx"] - 110.0
    bw = 220.0
    bh = 100.0
    print(f"Header {h['id']}: x=[{bx:.1f}, {bx+bw:.1f}], y=[{by}, {by+bh}]")
    for line in h["lines"]:
        est_w = len(line) * 0.6 * 30
        pad = (bw - est_w) / 2
        print(f"   line '{line}': est_w={est_w:.1f}px, pad={pad:.1f}px")
        assert pad >= 16.0, f"Pad {pad} < 16 for '{line}'!"

print("ALL HEADER PADDINGS >= 16px! (PASS)")
