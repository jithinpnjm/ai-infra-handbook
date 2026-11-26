#!/usr/bin/env python3

# Test all text padding across the entire SVG

def test_all():
    # Col 2: rect x = 365, w = 365 (x: 365..730, center = 547.5)
    # Col 3: rect x = 740, w = 385 (x: 740..1125, left pad relative to 740)
    # Col 4: rect x = 1135, w = 420 (x: 1135..1555, left pad relative to 1135)
    # Footer: rect x = 45, w = 1510 (x: 45..1555)

    print("=== COLUMN 2 (Source API, centered at 547.5, box 365..730) ===")
    c2_items = [
        ("metrics.k8s.io", 25, True),
        ("metrics.k8s.io", 24, True),
        ("per container", 24, False),
        ("custom.metrics.k8s.io", 24, True),
        ("custom.metrics.k8s.io", 24, True),
        ("for one object", 24, False),
        ("external.metrics.k8s.io", 24, True)
    ]
    for text, fs, is_mono in c2_items:
        factor = 0.62 if is_mono else 0.60
        w = len(text) * factor * fs
        left = 547.5 - w / 2
        right = 547.5 + w / 2
        pad_l = left - 365
        pad_r = 730 - right
        print(f"  '{text}' (fs={fs}): w={w:5.1f} | pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f} | min_pad={min(pad_l, pad_r):4.1f}")
        assert min(pad_l, pad_r) >= 16

    print("\n=== COLUMN 3 (Provider, left x=758, box 740..1125) ===")
    c3_items = [
        ("metrics-server from", 24),
        ("kubelet and cAdvisor", 24),
        ("via Prometheus Adapter,", 24),
        ("KEDA or vendor adapters", 24),
        ("via KEDA, Prometheus", 24),
        ("Adapter or cloud adapters", 24)
    ]
    for text, fs in c3_items:
        w = len(text) * 0.60 * fs
        pad_l = 758 - 740 # = 18 px
        pad_r = 1125 - (758 + w)
        print(f"  '{text}' (fs={fs}): w={w:5.1f} | pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f} | min_pad={min(pad_l, pad_r):4.1f}")
        assert pad_l >= 16 and pad_r >= 16

    print("\n=== COLUMN 4 (Example, left x=1155, box 1135..1555) ===")
    c4_items = [
        ("CPU or memory average", 24),
        ("utilisation relative to", 24),
        ("requests, or average value", 24),
        ("scale on the app container", 24),
        ("only, ignoring sidecars", 24),
        ("per-pod requests_in_flight", 24),
        ("or queue_length_per_pod", 24),
        ("Ingress", 24),
        ("requests_per_second", 24),
        ("SQS queue length, Pub/Sub", 24),
        ("backlog, global QPS", 24)
    ]
    for text, fs in c4_items:
        w = len(text) * 0.60 * fs
        pad_l = 1155 - 1135 # = 20 px
        pad_r = 1555 - (1155 + w)
        print(f"  '{text}' (fs={fs}): w={w:5.1f} | pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f} | min_pad={min(pad_l, pad_r):4.1f}")
        assert pad_l >= 16 and pad_r >= 16

    print("\n=== FOOTER RULES (box 45..1555, icon at 64..104, text at 126) ===")
    f_items = [
        ("utilisation metrics need requests on all containers or the metric is unavailable", 24),
        ("memory is a poor scaling signal because it does not fall after load drops", 24),
        ("freshness delay: metrics-server scrapes kubelets about every 15 s,", 24),
        ("custom metrics add the Prometheus scrape interval of 15 to 30 s plus the adapter", 24)
    ]
    for text, fs in f_items:
        w = len(text) * 0.60 * fs
        pad_l = 126 - 104 # gap from icon = 22 px
        pad_r = 1555 - (126 + w)
        print(f"  '{text[:40]}...' (fs={fs}): w={w:6.1f} | pad_l={pad_l:4.1f}, pad_r={pad_r:4.1f} | min_pad={min(pad_l, pad_r):4.1f}")
        assert pad_l >= 16 and pad_r >= 16

    print("\nALL PADDING CHECKS PASSED (MIN PAD >= 16 PX EVERYWHERE)!")

test_all()
