#!/usr/bin/env python3

boxes = [
    ("Box 1", 50, 290, [
        "crictl pods ",
        "--name trainer-0"
    ]),
    ("Box 2", 360, 320, [
        "crictl inspectp ",
        "<pod-id> | ",
        "jq .info.pid"
    ]),
    ("Box 3", 700, 380, [
        "nsenter -t <pid> -n ",
        "ip -br addr, ",
        "ip route, ss -tulpn"
    ]),
    ("Box 4", 1100, 450, [
        "kubectl debug -it ",
        "trainer-0 ",
        "--image=nicolaka/netshoot ",
        "--target=pytorch"
    ])
]

for name, x, w, lines in boxes:
    print(f"\n{name} (w={w}, min pad target=16):")
    for l in lines:
        tw = len(l) * 0.62 * 24
        pad = (w - tw) / 2 # if centered
        print(f"  '{l}': len={len(l)}, width={tw:.1f}px, padding={pad:.1f}px (fits? {pad >= 16})")
