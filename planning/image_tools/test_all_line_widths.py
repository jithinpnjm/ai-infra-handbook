#!/usr/bin/env python3

# Let's test all text lines and boxes in detail!

cols = {
    "pre_tasks": (45, 360),
    "tasks": (430, 425),
    "handlers": (880, 325),
    "post_tasks": (1230, 325)
}

# In each column, let's say the inner card has:
# card_x = col_x + 15
# card_w = col_w - 30
# Inside card:
# icon is at card_x + 14, size 44px (or 48px).
# text starts at card_x + 14 + 48 + 12 = card_x + 74.
# text available width = card_w - 74 - 16 = card_w - 90!
# Or if icon is not beside text, text starts at card_x + 16, avail_w = card_w - 32.

def check_card(col_name, title, lines, is_mono, icon_beside=True):
    col_x, col_w = cols[col_name]
    card_x = col_x + 15
    card_w = col_w - 30
    
    if icon_beside:
        text_x = card_x + 74
        avail_w = card_w - (74 + 16)
    else:
        text_x = card_x + 16
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
    # Col 1: pre_tasks (card_w = 330)
    ("pre_tasks", "assert app_version is a tag or commit SHA", 
     ["assert app_version", "is a tag or commit SHA"], False, True),
    ("pre_tasks", "touch drain flag under /var/www/lb-drain delegated to the first web host",
     ["touch drain flag under", "/var/www/lb-drain", "delegated to the", "first web host"], False, True),
    ("pre_tasks", "pause 5 seconds",
     ["pause 5 seconds"], False, True),
     
    # Col 2: tasks (card_w = 395, avail_w with icon beside = 395 - 90 = 305 px)
    ("tasks", "group and user", ["group and user"], False, True),
    ("tasks", "directory skeleton", ["directory skeleton"], False, True),
    ("tasks", "git fetch pinned version", ["git fetch", "pinned version"], False, True),
    ("tasks", "venv from requirements.lock", ["venv from", "requirements.lock"], False, True),
    ("tasks", "env file mode 0600", ["env file mode 0600"], False, True),
    ("tasks", "alembic upgrade head run_once", ["alembic upgrade head", "run_once"], False, True),
    ("tasks", "systemd unit", ["systemd unit"], False, True),
    ("tasks", "switch current symlink", ["switch current symlink"], False, True),
    ("tasks", "meta flush_handlers", ["meta flush_handlers"], False, True),
    ("tasks", "uri readyz retries 20 delay 3", ["uri readyz", "retries 20 delay 3"], False, True),
    ("tasks", "prune old releases", ["prune old releases"], False, True),
    
    # Col 3: handlers (card_w = 295, avail_w = 205 with icon beside)
    # What if in handlers, icon is at the top or beside?
    # If icon is beside: 205 px. Longest line: 'something changed' (17 * 14.4 = 244 px > 205 px).
    # If icon is placed at the top (centered), then avail_w = 295 - 32 = 263 px!
    # Let's test with icon above for handlers:
    ("handlers", "restart fleetapp only when something changed",
     ["restart fleetapp", "only when", "something changed"], False, False),
     
    # Col 4: post_tasks (card_w = 295)
    ("post_tasks", "remove drain flag", ["remove drain flag"], False, True),
    ("post_tasks", "host back in rotation", ["host back in rotation"], False, True),
]

passed = True
for col, title, lines, is_mono, icon_beside in items:
    ok = check_card(col, title, lines, is_mono, icon_beside)
    if not ok:
        passed = False

print("\n===============================")
print("All lines passed padding check?", passed)
