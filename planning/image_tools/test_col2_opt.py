# Column 2 simulation

start_y = 105

cards_col2 = [
    {
        "id": "card-6",
        "h": 220,
        "title_lines": ["Kernel network counters: "],
        "cmd_lines": [
            "ip -s link, nstat, conntrack -S, ethtool -S, ",
            "iptables-save, nft list ruleset, ipvsadm -Ln"
        ]
    },
    {
        "id": "card-7",
        "h": 220,
        "title_lines": ["Storage: "],
        "cmd_lines": [
            "findmnt, lsblk, df -hT, df -i, iostat -x, ",
            "fio"
        ]
    },
    {
        "id": "card-8",
        "h": 220,
        "title_lines": ["CPU, memory, I/O of the process: "],
        "cmd_lines": [
            "top -H, pidstat, perf, strace, py-spy, gdb"
        ]
    },
    {
        "id": "card-9",
        "h": 235,
        "title_lines": ["GPU and fabric: "],
        "cmd_lines": [
            "nvidia-smi, dcgmi, journalctl -k grep Xid, ",
            "lspci -vv, ibstat, all_reduce_perf"
        ]
    }
]

# Total card height = 220 + 220 + 220 + 235 = 895
# Total span = 1045
# Remaining for 3 gaps = 1045 - 895 = 150
# Each gap = 150 / 3 = 50px (>= 40px!)

curr_y = start_y
gap = 50

for c in cards_col2:
    c['y'] = curr_y
    c['x'] = 820
    c['w'] = 740
    
    title_bottom = curr_y + 38 + (len(c['title_lines']) - 1) * 32
    cmd_base_1 = title_bottom + 36
    cmd_bottom = cmd_base_1 + (len(c['cmd_lines']) - 1) * 28
    
    actual_bottom = cmd_bottom + 6
    bottom_pad = (curr_y + c['h']) - actual_bottom
    
    print(f"{c['id']} (y={curr_y}, h={c['h']}): text bottom={actual_bottom}, bottom_pad={bottom_pad:.1f}px")
    assert bottom_pad >= 16, f"Failed bottom pad in {c['id']}: {bottom_pad}"
    
    curr_y += c['h'] + gap

print("\nCol 2 all passed!")
print(f"Col 2 ended at y = {curr_y - gap}, bottom margin = {1200 - (curr_y - gap)}px")
