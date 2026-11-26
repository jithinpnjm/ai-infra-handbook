def check_fit(lines, box_w, fs, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    max_line_w = 0
    worst_line = ""
    for l in lines:
        w = len(l) * factor * fs
        if w > max_line_w:
            max_line_w = w
            worst_line = l
    avail_w = box_w - 32 # 16px padding on each side
    fit = max_line_w <= avail_w
    return fit, max_line_w, avail_w, worst_line

# Let's test the layout dimensions:
# Table layout:
# Total canvas width = 1600
# Margin left = 40, right = 40
# Timeline left panel: x = 40, width = 310
# Gap = 30
# Table start x = 380, total table width = 1180 (x from 380 to 1560)
# Columns:
# Col 1: width = 320 (x: 380 .. 700)
# Gap = 15
# Col 2: width = 460 (x: 715 .. 1175)
# Gap = 15
# Col 3: width = 370 (x: 1190 .. 1560)
# Total table width = 320 + 15 + 460 + 15 + 370 = 1180. 380 + 1180 = 1560! Perfect.

cols = {
    "col1": 320,
    "col2": 460,
    "col3": 370,
    "timeline": 310,
    "title": 1520,
    "bottom_bar": 1520
}

# Now let's define the line wraps for each label:
wraps = {
    "title": (["What the client sees when a connection fails, and where to look"], 1520, 48, False),
    "header1": (["Error the", "client sees"], 320, 30, False),
    "header2": (["What actually happened on the wire"], 460, 26, False),
    "header3": (["Where to look"], 370, 30, False),
    
    # Row 1
    "r1_c1": (["Connection refused", "(ECONNREFUSED)"], 320, 26, False),
    "r1_c2": ([
        "a RST came back: host reachable,",
        "nobody listening on that port, or a",
        "firewall using reject --tcp-reset"
    ], 460, 24, False),
    "r1_c3": ([
        "the listener: somebody",
        "was home and said no"
    ], 370, 24, False),

    # Row 2
    "r2_c1": (["Connection timed out", "(ETIMEDOUT)"], 320, 26, False),
    "r2_c2": ([
        "no reply to the SYNs, retried with",
        "exponential backoff 1, 2, 4 seconds",
        "and so on; tcp_syn_retries=6",
        "gives about 127 seconds"
    ], 460, 24, False),
    "r2_c3": ([
        "route and firewall or security",
        "group, host down: nobody",
        "answered the door at all"
    ], 370, 24, False),

    # Row 3
    "r3_c1": ([
        "No route to host or",
        "Network is unreachable"
    ], 320, 24, False),
    "r3_c2": ([
        "ICMP unreachable from a router,",
        "or no local route"
    ], 460, 24, False),
    "r3_c3": ([
        "the routing table",
        "(chapter 2.5)"
    ], 370, 24, False),

    # Row 4
    "r4_c1": ([
        "Connection reset",
        "by peer"
    ], 320, 26, False),
    "r4_c2": ([
        "a RST during an established",
        "connection"
    ], 460, 24, False),
    "r4_c3": ([
        "peer crashed, app closed with unread",
        "data, firewall or NAT state expired,",
        "load balancer idle timeout"
    ], 370, 24, False),

    # Timeline labels
    "tl_retried": (["SYN retried"], 310, 26, False),
    "tl_refused": (["SYN then RST"], 310, 26, False),

    # Bottom bar
    "bottom": ([
        "A refusal means the host answered, so look at the listener; a timeout means",
        "the SYNs never got a reply, so look at the route and firewall"
    ], 1520, 26, False)
}

all_ok = True
for key, (lines, box_w, fs, is_mono) in wraps.items():
    fit, max_w, avail, worst = check_fit(lines, box_w, fs, is_mono)
    status = "OK" if fit else "FAIL"
    if not fit:
        all_ok = False
    print(f"[{status:4s}] {key:12s}: box_w={box_w:4d}, max_line_w={max_w:6.1f}, avail={avail:6.1f}, fs={fs:2d} | '{worst}'")

print(f"\nOverall fit: {'ALL PASSED' if all_ok else 'SOME FAILED'}")
