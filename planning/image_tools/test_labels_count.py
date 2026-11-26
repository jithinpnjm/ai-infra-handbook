#!/usr/bin/env python3

labels = [
    "One app host through the application play",
    "one app host with serial one at a time and max_fail_percentage 0",
    "pre_tasks",
    "assert app_version is a tag or commit SHA",
    "touch drain flag under /var/www/lb-drain delegated to the first web host",
    "pause 5 seconds",
    "tasks",
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
    "prune old releases",
    "handlers",
    "restart fleetapp only when something changed",
    "post_tasks",
    "remove drain flag",
    "host back in rotation"
]

print("Total labels count:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. {l}")
