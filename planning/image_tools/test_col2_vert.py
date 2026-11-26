#!/usr/bin/env python3

# Let's test the vertical budget in Column 2 (tasks):
# y starts at 220, ends by 1165. Total height = 945 px.

items = [
    ("group and user", 1),
    ("directory skeleton", 1),
    ("git fetch pinned version", 2),
    ("venv from requirements.lock", 2),
    ("env file mode 0600", 1),
    ("alembic upgrade head run_once", 2),
    ("systemd unit", 1),
    ("switch current symlink", 2),
    ("meta flush_handlers", 1),
    ("uri readyz retries 20 delay 3", 2),
    ("prune old releases", 1),
]

# Height of 1-line card: 62 px
# Height of 2-line card: 84 px

gap = 12
current_y = 220
print("Column 2 cards:")
for title, n_lines in items:
    h = 62 if n_lines == 1 else 84
    print(f"  y={current_y:4d}, h={h:2d}, y_end={current_y+h:4d} | {title} ({n_lines} lines)")
    current_y += h + gap

total_h = (current_y - gap) - 220
print(f"\nTotal tasks stack height: {total_h} px. Ends at y = {current_y - gap} (budget up to 1165)")
print(f"Remaining bottom space: {1165 - (current_y - gap)} px")
