#!/usr/bin/env python3

def verify():
    # Columns:
    # Col 1: x = 45, width = 300 (x_end = 345)
    # Col 2: x = 355, width = 375 (x_end = 730)
    # Col 3: x = 740, width = 395 (x_end = 1135)
    # Col 4: x = 1145, width = 410 (x_end = 1555)

    cols = {
        1: (45, 300),
        2: (355, 375),
        3: (740, 395),
        4: (1145, 410)
    }

    # Test all text items:
    items = [
        # Headers:
        ("Header Col 1", 1, ["Type"], 30, False, False),
        ("Header Col 2", 2, ["Source API"], 30, False, False),
        ("Header Col 3", 3, ["Provider"], 30, False, False),
        ("Header Col 4", 4, ["Example"], 30, False, False),

        # Row 1:
        ("R1 Type", 1, ["Resource"], 26, True, False), # with icon
        ("R1 API", 2, ["metrics.k8s.io"], 24, False, True),
        ("R1 Provider", 3, ["metrics-server from", "kubelet and cAdvisor"], 24, False, False),
        ("R1 Example", 4, ["CPU or memory average", "utilisation relative to", "requests, or average value"], 24, False, False),

        # Row 2:
        ("R2 Type", 1, ["ContainerResource"], 25, True, False),
        ("R2 API", 2, ["metrics.k8s.io", "per container"], 24, False, False),
        ("R2 Example", 4, ["scale on the app container", "only, ignoring sidecars"], 24, False, False),

        # Row 3:
        ("R3 Type", 1, ["Pods"], 26, True, False),
        ("R3 API", 2, ["custom.metrics.k8s.io"], 24, False, True),
        ("R3 Provider", 3, ["via Prometheus Adapter,", "KEDA or vendor adapters"], 24, False, False),
        ("R3 Example", 4, ["per-pod requests_in_flight", "or queue_length_per_pod"], 24, False, False),

        # Row 4:
        ("R4 Type", 1, ["Object"], 26, True, False),
        ("R4 API", 2, ["custom.metrics.k8s.io", "for one object"], 24, False, False),
        ("R4 Example", 4, ["Ingress requests_per_second"], 24, False, False),

        # Row 5:
        ("R5 Type", 1, ["External"], 26, True, False),
        ("R5 API", 2, ["external.metrics.k8s.io"], 24, False, True),
        ("R5 Provider", 3, ["via KEDA, Prometheus", "Adapter or cloud adapters"], 24, False, False),
        ("R5 Example", 4, ["SQS queue length, Pub/Sub", "backlog, global QPS"], 24, False, False),
    ]

    all_passed = True
    for label, col_idx, lines, fs, has_icon, is_mono in items:
        x, w = cols[col_idx]
        padding = 16
        avail_w = w - 2 * padding
        if has_icon:
            # If icon is on the left: icon takes 52px + 12px gap = 64px
            # Or if icon is above the text, avail_w is unchanged!
            # Let's test if icon is on the left vs above:
            avail_w_beside = avail_w - 64
        else:
            avail_w_beside = avail_w

        factor = 0.62 if is_mono else 0.60
        for line in lines:
            lw = len(line) * factor * fs
            # check beside icon for Col 1
            lim = avail_w_beside if has_icon else avail_w
            ok = (lw <= lim)
            if not ok:
                # If beside icon overflows, let's see if placing icon above works:
                ok_above = (lw <= avail_w)
                if ok_above:
                    print(f"[ICON ABOVE] {label}: line '{line}' lw={lw:.1f} fits in {avail_w} (cannot fit beside icon {avail_w_beside:.1f})")
                else:
                    print(f"[FAILED] {label}: line '{line}' lw={lw:.1f} > {avail_w:.1f}")
                    all_passed = False
            else:
                print(f"[OK] {label}: line '{line}' lw={lw:.1f} <= {lim:.1f}")

    print("All items verified?", all_passed)

verify()
