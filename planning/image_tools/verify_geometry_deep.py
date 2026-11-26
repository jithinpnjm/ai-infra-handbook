#!/usr/bin/env python3

card_checks = [
    ("pretask-1", (60, 226, 330, 180), [
        ("assert app_version", 24, False, 225, 322, "middle"),
        ("is a tag or", 24, False, 225, 350, "middle"),
        ("commit SHA", 24, False, 225, 378, "middle")
    ]),
    ("pretask-2", (60, 430, 330, 240), [
        ("touch drain flag", 24, False, 225, 520, "middle"),
        ("under", 24, False, 225, 548, "middle"),
        ("/var/www/lb-drain", 24, True, 225, 576, "middle"),
        ("delegated to the", 24, False, 225, 604, "middle"),
        ("first web host", 24, False, 225, 632, "middle")
    ]),
    ("pretask-3", (60, 694, 330, 130), [
        ("pause 5 seconds", 24, False, 225, 788, "middle")
    ]),
    ("task-1", (445, 218, 395, 66), [
        ("group and user", 24, False, 525, 259, "start")
    ]),
    ("task-2", (445, 294, 395, 66), [
        ("directory skeleton", 24, False, 525, 335, "start")
    ]),
    ("task-3", (445, 370, 395, 92), [
        ("git fetch", 24, False, 525, 407, "start"),
        ("pinned version", 24, False, 525, 435, "start")
    ]),
    ("task-4", (445, 472, 395, 92), [
        ("venv from", 24, False, 525, 509, "start"),
        ("requirements.lock", 24, True, 525, 537, "start")
    ]),
    ("task-5", (445, 574, 395, 66), [
        ("env file mode 0600", 24, True, 525, 615, "start")
    ]),
    ("task-6", (445, 650, 395, 92), [
        ("alembic upgrade head", 24, True, 525, 687, "start"),
        ("run_once", 24, True, 525, 715, "start")
    ]),
    ("task-7", (445, 752, 395, 66), [
        ("systemd unit", 24, False, 525, 793, "start")
    ]),
    ("task-8", (445, 828, 395, 92), [
        ("switch current", 24, False, 525, 865, "start"),
        ("symlink", 24, False, 525, 893, "start")
    ]),
    ("task-9", (445, 930, 395, 66), [
        ("meta flush_handlers", 24, True, 525, 971, "start")
    ]),
    ("task-10", (445, 1006, 395, 92), [
        ("uri readyz", 24, True, 525, 1043, "start"),
        ("retries 20 delay 3", 24, True, 525, 1071, "start")
    ]),
    ("task-11", (445, 1108, 395, 66), [
        ("prune old releases", 24, False, 525, 1149, "start")
    ]),
    ("handler-card", (895, 875, 295, 190), [
        ("restart fleetapp", 24, False, 1042, 975, "middle"),
        ("only when", 24, False, 1042, 1003, "middle"),
        ("something changed", 24, False, 1042, 1031, "middle")
    ]),
    ("posttask-1", (1245, 940, 295, 100), [
        ("remove drain flag", 24, False, 1392, 1018, "middle")
    ]),
    ("posttask-2", (1245, 1062, 295, 90), [
        ("host back in", 24, False, 1312, 1099, "start"),
        ("rotation", 24, False, 1312, 1127, "start")
    ]),
]

print("Checking padding on all card text lines:")
all_ok = True
for card_id, (cx, cy, cw, ch), lines in card_checks:
    card_x2 = cx + cw
    card_y2 = cy + ch
    for l, fs, is_mono, tx, ty, anchor in lines:
        rate = 0.62 if is_mono else 0.60
        lw = len(l) * rate * fs
        if anchor == "middle":
            lx1 = tx - lw / 2
            lx2 = tx + lw / 2
        else:
            lx1 = tx
            lx2 = tx + lw
        ly1 = ty - fs * 0.8
        ly2 = ty + fs * 0.2
        
        pad_left = lx1 - cx
        pad_right = card_x2 - lx2
        pad_top = ly1 - cy
        pad_bottom = card_y2 - ly2
        
        min_pad = min(pad_left, pad_right, pad_top, pad_bottom)
        ok = min_pad >= 16
        if not ok:
            all_ok = False
        print(f"[{'OK' if ok else 'FAIL'}] {card_id:12s} | '{l}': min_pad={min_pad:.1f}px (L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f})")

print("\nAll cards padding >= 16px?", all_ok)
