#!/usr/bin/env python3

cols = {
    "pre_tasks": (45, 360),
    "tasks": (430, 425),
    "handlers": (880, 325),
    "post_tasks": (1230, 325)
}

def check_line(col_name, title, lines, is_mono, icon_beside):
    col_x, col_w = cols[col_name]
    card_w = col_w - 30
    if icon_beside:
        avail_w = card_w - 90
    else:
        avail_w = card_w - 32
    
    fs = 24
    rate = 0.62 if is_mono else 0.60
    
    print(f"\n[{col_name}] {title} (avail_w = {avail_w:.1f} px):")
    all_ok = True
    for l in lines:
        w = len(l) * rate * fs
        ok = (w <= avail_w)
        if not ok:
            all_ok = False
        print(f"  [{'OK' if ok else 'FAIL'}] '{l}': w={w:.1f} <= {avail_w:.1f} (diff={avail_w - w:.1f})")
    return all_ok

items = [
    # Col 1: pre_tasks (card_w = 330, avail_w = 298 px)
    ("pre_tasks", "assert app_version is a tag or commit SHA", 
     ["assert app_version", "is a tag or", "commit SHA"], False, False),
    ("pre_tasks", "touch drain flag under /var/www/lb-drain delegated to the first web host",
     ["touch drain flag", "under", "/var/www/lb-drain", "delegated to the", "first web host"], False, False),
    ("pre_tasks", "pause 5 seconds",
     ["pause 5 seconds"], False, False),
     
    # Col 2: tasks (card_w = 395, avail_w with icon beside = 305 px)
    ("tasks", "group and user", ["group and user"], False, True),
    ("tasks", "directory skeleton", ["directory skeleton"], False, True),
    ("tasks", "git fetch pinned version", ["git fetch", "pinned version"], False, True),
    ("tasks", "venv from requirements.lock", ["venv from", "requirements.lock"], False, True),
    ("tasks", "env file mode 0600", ["env file mode 0600"], False, True),
    ("tasks", "alembic upgrade head run_once", ["alembic upgrade head", "run_once"], False, True),
    ("tasks", "systemd unit", ["systemd unit"], False, True),
    ("tasks", "switch current symlink", ["switch current", "symlink"], False, True),
    ("tasks", "meta flush_handlers", ["meta flush_handlers"], False, True),
    ("tasks", "uri readyz retries 20 delay 3", ["uri readyz", "retries 20 delay 3"], False, True),
    ("tasks", "prune old releases", ["prune old releases"], False, True),
    
    # Col 3: handlers (card_w = 295, avail_w = 263 px)
    ("handlers", "restart fleetapp only when something changed",
     ["restart fleetapp", "only when", "something changed"], False, False),
     
    # Col 4: post_tasks (card_w = 295, avail_w = 263 px)
    ("post_tasks", "remove drain flag", ["remove drain flag"], False, False),
    ("post_tasks", "host back in rotation", ["host back", "in rotation"], False, False),
]

all_passed = True
for col, title, lines, is_mono, icon_beside in items:
    ok = check_line(col, title, lines, is_mono, icon_beside)
    if not ok:
        all_passed = False

print("\n===============================")
print("ALL LINES PASSED PADDING CHECK?", all_passed)
