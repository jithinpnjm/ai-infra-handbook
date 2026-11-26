#!/usr/bin/env python3

def check_wrap(name, lines, max_w, fs=24, is_mono=False):
    coeff = 0.62 if is_mono else 0.60
    print(f"\n--- Checking {name} (box_w={max_w}, fs={fs}, {'mono' if is_mono else 'sans'}) ---")
    all_ok = True
    for i, line in enumerate(lines, 1):
        w = len(line) * fs * coeff
        pad = (max_w - w) / 2
        ok = pad >= 16.0
        print(f"  Line {i}: '{line}' | w={w:.1f}px, pad={pad:.1f}px [{'OK' if ok else 'FAIL'}]")
        if not ok: all_ok = False
    return all_ok

# Side Note 1 (box_w = 560):
# "resourceVersion is opaque, compare only for equality, derived from the etcd mod_revision"
check_wrap("Side Note 1", [
    "resourceVersion is opaque,",
    "compare only for equality,",
    "derived from the etcd mod_revision"
], 560)

# Side Note 2 (box_w = 480):
# "uid identifies one instance; a recreated object gets a new uid"
check_wrap("Side Note 2", [
    "uid identifies one instance;",
    "a recreated object gets a new uid"
], 480)

# Side Note 3 (box_w = 420):
# "kubectl rollout status uses this"
check_wrap("Side Note 3", [
    "kubectl rollout status",
    "uses this"
], 420, is_mono=True)

check_wrap("Side Note 3 (sans)", [
    "kubectl rollout status uses this"
], 420, fs=24)
