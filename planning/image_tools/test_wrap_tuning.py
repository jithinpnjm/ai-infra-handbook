# Let's find ideal line breaks for every cell

def eval_cell(lines, bw, bh, fs, left_pad=24, line_h=28):
    print(f"--- Cell (bw={bw}, bh={bh}, fs={fs}) ---")
    all_ok = True
    total_text_h = len(lines) * line_h
    avail_h = bh - total_text_h
    v_pad = avail_h / 2
    if v_pad < 16:
        print(f"  V-PAD FAIL: v_pad={v_pad:.1f} < 16 (total_h={total_text_h}, bh={bh})")
        all_ok = False
    else:
        print(f"  V-PAD OK: v_pad={v_pad:.1f} >= 16")

    for l in lines:
        w = len(l) * 0.6 * fs
        right_pad = bw - left_pad - w
        if right_pad < 16:
            print(f"  H-PAD FAIL: right_pad={right_pad:.1f} < 16 on '{l}' (w={w:.1f})")
            all_ok = False
        else:
            print(f"  H-PAD OK: right_pad={right_pad:.1f} >= 16 on '{l}'")
    return all_ok

cells = {
    # Row 1 Col 2
    "r1_c2": ([
        "a RST came back: host reachable,",
        "nobody listening on that port,",
        "or a firewall using reject",
        "--tcp-reset"
    ], 480, 190, 24),
    
    # Row 1 Col 3
    "r1_c3": ([
        "the listener: somebody",
        "was home and said no"
    ], 360, 190, 24),

    # Row 2 Col 2
    "r2_c2": ([
        "no reply to the SYNs, retried",
        "with exponential backoff 1, 2, 4",
        "seconds and so on; tcp_syn_retries=6",
        "gives about 127 seconds"
    ], 480, 195, 24),

    # Row 2 Col 3
    "r2_c3": ([
        "route and firewall or security",
        "group, host down: nobody",
        "answered the door at all"
    ], 360, 195, 24),

    # Row 3 Col 2
    "r3_c2": ([
        "ICMP unreachable from a",
        "router, or no local route"
    ], 480, 185, 24),

    # Row 3 Col 3
    "r3_c3": ([
        "the routing table",
        "(chapter 2.5)"
    ], 360, 185, 24),

    # Row 4 Col 2
    "r4_c2": ([
        "a RST during an",
        "established connection"
    ], 480, 185, 24),

    # Row 4 Col 3
    "r4_c3": ([
        "peer crashed, app closed with",
        "unread data, firewall or NAT",
        "state expired, load balancer",
        "idle timeout"
    ], 360, 185, 24)
}

all_pass = True
for name, (lines, bw, bh, fs) in cells.items():
    print(f"\nChecking {name}:")
    ok = eval_cell(lines, bw, bh, fs)
    if not ok: all_pass = False

print(f"\nOverall: {'ALL CELLS PASS' if all_pass else 'SOME CELLS FAIL'}")
