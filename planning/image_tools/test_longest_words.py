#!/usr/bin/env python3

labels = [
    ("One app host through the application play", False),
    ("one app host with serial one at a time and max_fail_percentage 0", False),
    ("pre_tasks", True),
    ("assert app_version is a tag or commit SHA", False),
    ("touch drain flag under /var/www/lb-drain delegated to the first web host", False),
    ("pause 5 seconds", False),
    ("tasks", True),
    ("group and user", False),
    ("directory skeleton", False),
    ("git fetch pinned version", False),
    ("venv from requirements.lock", False),
    ("env file mode 0600", False),
    ("alembic upgrade head run_once", False),
    ("systemd unit", False),
    ("switch current symlink", False),
    ("meta flush_handlers", False),
    ("uri readyz retries 20 delay 3", False),
    ("prune old releases", False),
    ("handlers", True),
    ("restart fleetapp only when something changed", False),
    ("post_tasks", True),
    ("remove drain flag", False),
    ("host back in rotation", False),
]

print("Max word/token length per label:")
for l, _ in labels:
    words = l.split()
    longest = max(words, key=len)
    w = len(longest) * 0.62 * 24 # conservative monospace rate
    print(f"'{l[:35]:35s}' | longest: '{longest:20s}' (len {len(longest):2d}) | min width needed: {w+32:.1f} px")
