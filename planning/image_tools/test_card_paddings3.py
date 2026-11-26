import textwrap

cards_def = [
    {
        "id": 1,
        "col": 0, "row": 0,
        "title": [
            "1 Invalid authentication credential",
            "or Unable to contact",
            "slurm controller:"
        ],
        "body": [
            "different munge keys, clock skew over a",
            "few minutes, munged not running, wrong",
            "permissions on /etc/munge or /run/munge"
        ],
        "orange": True,
        "icon": "shield"
    },
    {
        "id": 2,
        "col": 1, "row": 0,
        "title": [
            "2 Node invalid or drain with Low",
            "RealMemory:"
        ],
        "body": [
            "node line does not match what slurmd",
            "discovers; run slurmd -C"
        ],
        "orange": False,
        "icon": "ram"
    },
    {
        "id": 3,
        "col": 0, "row": 1,
        "title": [
            "3 Jobs rejected or sacctmgr hangs,",
            "Invalid account or",
            "account/partition combination:"
        ],
        "body": [
            "slurmdbd not running, wrong DB credentials,",
            "max_allowed_packet too small, blocked port,",
            "no association; follow the request: command",
            "to slurmdbd to database to login"
        ],
        "orange": False,
        "icon": "db"
    },
    {
        "id": 4,
        "col": 1, "row": 1,
        "title": [
            "4 Controller will not start or empty",
            "queue:"
        ],
        "body": [
            "StateSaveLocation not writable, full, not",
            "shared, wiped"
        ],
        "orange": False,
        "icon": "disk"
    },
    {
        "id": 5,
        "col": 0, "row": 2,
        "title": [
            "5 Can't find an address, wrong user,",
            "Invalid user id:"
        ],
        "body": [
            "NodeName differs from hostname with no",
            "NodeHostname or NodeAddr, DNS or hosts",
            "inconsistencies, UID mismatch"
        ],
        "orange": False,
        "icon": "id"
    },
    {
        "id": 6,
        "col": 1, "row": 2,
        "title": [
            "6 slurmd will not start after an OS",
            "upgrade:"
        ],
        "body": [
            "OS switched to cgroup v2 while Slurm built",
            "without v2, cgroup.conf forces v1, missing",
            "systemd delegation; stat -fc %T",
            "/sys/fs/cgroup"
        ],
        "orange": False,
        "icon": "gear"
    },
    {
        "id": 7,
        "col": 0, "row": 3,
        "title": [
            "7 Socket timed out on send/recv",
            "operation:"
        ],
        "body": [
            "polling loops from hundreds of clients",
            "running squeue every second, too small",
            "MaxJobCount, accounting back-pressure; run",
            "sdiag, look at RPC statistics by type and",
            "by user; use sacct for history, exporters",
            "that poll once, RPC rate limiting"
        ],
        "orange": False,
        "icon": "clock"
    },
    {
        "id": 8,
        "col": 1, "row": 3,
        "title": [
            "8 squeue and sinfo time out but",
            "running jobs continue:"
        ],
        "body": [
            "accounting database under strain, very",
            "wide sacct or sreport query; sdiag thread",
            "count and agent queue, slurmdbd.log lock",
            "waits, SHOW FULL PROCESSLIST in the",
            "database"
        ],
        "orange": False,
        "icon": "lockdb"
    }
]

# Total height = 1200
row_y = [75, 320, 565, 805]
row_h = [230, 230, 225, 275]

cw = 740
for c in cards_def:
    cid = c["id"]
    cx = 40 if c["col"] == 0 else 820
    cy = row_y[c["row"]]
    ch = row_h[c["row"]]
    
    ix = cx + 16
    iy = cy + 16
    iw = 44
    ih = 44
    
    tx = cx + 76
    clearance_left = (tx - (ix + iw))
    assert clearance_left >= 16, f"Left clearance {clearance_left} < 16"
    
    first_y = cy + 38
    cur_y = first_y
    
    print(f"\n--- Card {cid} (x={cx}, y={cy}, w={cw}, h={ch}) ---")
    print(f"  Icon at ({ix}, {iy}, w={iw}), Text start x={tx} (clearance={clearance_left}px)")
    
    for i, tl in enumerate(c["title"]):
        if i > 0:
            cur_y += 34
        # 30px bold: 18.0 px/char (0.6 * 30)
        w = len(tl) * 18.0
        pad_right = (cx + cw) - (tx + w)
        print(f"  [T{i+1}] len={len(tl):2d}, w={w:5.1f}px, right_pad={pad_right:4.1f}px | {tl}")
        assert pad_right >= 16, f"Right pad {pad_right} < 16"
        
    for j, bl in enumerate(c["body"]):
        cur_y += 28
        # 24px: 0.6 * 24 = 14.4 px/char, monospace commands 0.62 * 24 = 14.88 px/char
        char_scale = 14.88 if ('stat -fc' in bl or 'slurmd -C' in bl) else 14.4
        w = len(bl) * char_scale
        pad_right = (cx + cw) - (tx + w)
        print(f"  [B{j+1}] len={len(bl):2d}, w={w:5.1f}px, right_pad={pad_right:4.1f}px | {bl}")
        assert pad_right >= 16, f"Right pad {pad_right} < 16"
        
    pad_bottom = (cy + ch) - (cur_y + 6)
    print(f"  Bottom pad = {pad_bottom:.1f}px")
    assert pad_bottom >= 16, f"Bottom pad {pad_bottom} < 16"

# Check Takeaway bar
# Row 3 bottom = 805 + 275 = 1080
# Takeaway bar: y = 1100, height = 70 -> bottom = 1170
# Bottom margin to 1200 = 30px
bar_y = 1100
bar_h = 70
assert bar_y - (row_y[3] + row_h[3]) >= 16
assert (1200 - (bar_y + bar_h)) >= 16
print("\nTakeaway bar y=1100, h=70 -> clearance top = 20px, bottom = 30px!")

print("\nALL 8 CARDS AND TAKEAWAY BAR HAVE ZERO OVERFLOW AND PERFECT >= 16 PX PADDING ON ALL SIDES!")
