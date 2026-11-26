#!/usr/bin/env python3

labels = [
    # pre_tasks
    ("assert app_version is a tag or commit SHA", False),
    ("touch drain flag under /var/www/lb-drain delegated to the first web host", False),
    ("pause 5 seconds", False),
    # tasks
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
    # post_tasks
    ("remove drain flag", False),
    ("host back in rotation", False),
    # handlers
    ("restart fleetapp only when something changed", False),
    # context
    ("one app host with serial one at a time and max_fail_percentage 0", False),
]

# Rule: sans 0.6 x font-size per char, mono 0.62 x font-size per char
# Box width if 4 columns: 360 px
# Available width inside box with 16px padding on each side: 360 - 32 = 328 px.
# If icon is beside text: icon 56px + gap 12px = 68px.
# If number circle is also beside text: r=24 -> diameter 48px + gap 10px = 58px.
# Then available width for text would be: 328 - 68 - 58 = 202 px!

print("Testing single-line widths at font-size 24:")
for text, is_mono in labels:
    factor = 0.62 if is_mono else 0.60
    w = len(text) * factor * 24
    print(f"w={w:5.1f} px | len={len(text):2d} | '{text}'")
