#!/usr/bin/env python3

# Let's list the exact items in tasks:
tasks = [
    "group and user",
    "directory skeleton",
    "git fetch pinned version",
    "venv from requirements.lock",
    "env file mode 0600",
    "alembic upgrade head run_once",
    "systemd unit",
    "switch current symlink",
    "meta flush_handlers",
    "uri readyz retries 20 delay 3",
    "prune old releases"
]

print("Count of tasks:", len(tasks))
for i, t in enumerate(tasks, 1):
    print(f"{i:2d}. {t} (len={len(t)})")
