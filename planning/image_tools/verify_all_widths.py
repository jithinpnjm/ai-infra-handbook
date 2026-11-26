def mono_w(text, fs=24):
    return len(text) * fs * 0.62

def sans_w(text, fs=24):
    return len(text) * fs * 0.60

lines = [
    # (name, text, fs, is_mono, max_width_available)
    ("Title", "Environment variables versus DNS for finding a Service", 48, False, 1600),
    ("Timeline 1 Heading", "Environment variables", 32, False, 1400),
    ("Service created at T1", "Service created at T1", 26, False, 400), # Icon above text!
    ("Pod T2 line 1", "pod created at T2 receives", 24, False, 900),
    ("Pod T2 line 2", "NGINX_SERVICE_HOST=10.110.34.183 and NGINX_SERVICE_PORT=80", 24, True, 900),
    ("Pod T2 line 3", "only for Services that existed before the pod", 24, False, 900),
    ("second pod line 1", "a second pod created before the Service", 24, False, 900),
    ("second pod line 2", "has no variables until it restarts", 24, False, 900),
    ("badge line 1", "badge printed at birth,", 24, False, 400),
    ("badge line 2", "never updated", 24, False, 400),
    ("large note line 1", "in a namespace with 2,000 Services kubelet injects 10,000+ variables,", 24, False, 1380),
    ("large note line 2", "which can exceed the Linux execve environment size limit (MAX_ARG_STRLEN)", 24, True, 1380),
    ("large note line 3", "and fail container start; set enableServiceLinks false", 24, True, 1380),
    ("Timeline 2 Heading", "DNS (CoreDNS)", 32, False, 1400),
    ("DNS item 1 line 1", "name my-svc.my-ns.svc.cluster.local resolves as soon as the Service exists;", 24, True, 1380),
    ("DNS item 1 line 2", "phone book anyone can look up any time", 24, False, 1380),
    ("DNS item 2", "A and AAAA for the ClusterIP, SRV for named ports; headless returns pod IPs", 24, False, 1380),
    ("Footer line 1", "Kubernetes annotation values must be quoted strings,", 24, False, 1400),
    ("Footer line 2", "the text true in quotes, not a bare YAML boolean", 24, False, 1400)
]

print("Checking widths with strict conservative estimates:")
for name, text, fs, is_mono, max_w in lines:
    w = (mono_w if is_mono else sans_w)(text, fs)
    padding = max_w - w
    print(f"{name:25s} | len={len(text):2d} | text_w={w:6.1f}px | max_w={max_w:6.1f}px | rem={padding:6.1f}px")
    assert padding >= 32, f"FAILED: {name} remaining space {padding} < 32px"

print("\nALL LINES COMFORTABLY PASS PADDING REQUIREMENTS (>= 16px on each side)!")
