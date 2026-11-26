# Let's optimize heights and gaps for Column 1 and Column 2

start_y = 105

# Col 1: 5 cards
# Gaps: 4 * 40 = 160
# Card 1: 220
# Card 2: 150
# Card 3: 185
# Card 4: 150
# Card 5: 180
# Total height = 220 + 150 + 185 + 150 + 180 = 885
# Total span = 885 + 160 = 1045
# End y = 105 + 1045 = 1150
# Bottom margin = 1200 - 1150 = 50px (>= 40px!)

# Let's verify each card in Col 1 with exact math:

cards_col1 = [
    {
        "id": "card-1",
        "h": 210,
        "title_lines": ["What does the runtime ", "think exists: "],
        "cmd_lines": [
            "crictl pods, crictl ps -a, crictl inspectp, ",
            "crictl inspect (pid, exit code, mounts, ",
            "resources), crictl logs, crictl stats; ",
            "ctr -n k8s.io tasks ls"
        ]
    },
    {
        "id": "card-2",
        "h": 160,
        "title_lines": ["What do the kubelet ", "and runtime say: "],
        "cmd_lines": [
            "journalctl -u kubelet -u containerd ",
            "--since -30 min"
        ]
    },
    {
        "id": "card-3",
        "h": 185,
        "title_lines": ["Which namespaces ", "does this process live in: "],
        "cmd_lines": [
            "lsns -p PID, ls -l /proc/PID/ns, ",
            "/proc/PID/cgroup; get PID with ",
            "crictl inspect template info.pid"
        ]
    },
    {
        "id": "card-4",
        "h": 150,
        "title_lines": ["What is the pod network doing: "],
        "cmd_lines": [
            "nsenter -t PID -n ip addr, ip route, ",
            "ss -tnap, tcpdump"
        ]
    },
    {
        "id": "card-5",
        "h": 180,
        "title_lines": ["What does the pod ", "filesystem look like: "],
        "cmd_lines": [
            "nsenter -t PID -m ls, cat /proc/mounts, ",
            "df -h"
        ]
    }
]

# Let's check clearances for Col 1
curr_y = start_y
for c in cards_col1:
    c['y'] = curr_y
    c['x'] = 40
    c['w'] = 740
    
    # Text calculation
    # Icon is at x = 40 + 18 = 58, y = curr_y + 16, w = 48, h = 48
    # Title x = 58 + 48 + 14 = 120
    # Title baseline 1: curr_y + 38
    # If 2 lines: line 2 baseline: curr_y + 38 + 32 = curr_y + 70
    title_bottom = curr_y + 38 + (len(c['title_lines']) - 1) * 32
    
    # Cmds start at x = 40 + 20 = 60
    # Cmd baseline 1: title_bottom + 34
    cmd_base_1 = title_bottom + 34
    cmd_bottom = cmd_base_1 + (len(c['cmd_lines']) - 1) * 27
    
    # Actual text bottom is baseline + ~6px
    actual_bottom = cmd_bottom + 6
    bottom_pad = (curr_y + c['h']) - actual_bottom
    
    print(f"{c['id']} (y={curr_y}, h={c['h']}): text bottom={actual_bottom}, bottom_pad={bottom_pad:.1f}px")
    assert bottom_pad >= 16, f"Failed bottom pad in {c['id']}: {bottom_pad}"
    
    curr_y += c['h'] + 40

print("\nCol 1 all passed!")
print(f"Col 1 ended at y = {curr_y - 40}, bottom margin = {1200 - (curr_y - 40)}px")
