items = [
    "--syntax-check (parse only, touches no host)",
    "--list-tasks --list-tags --list-hosts",
    "--check --diff --limit gpu001 (what would change)",
    "--step (confirm every task y/n/c)",
    "--start-at-task Install driver",
    "-t config -l gpu001",
    "ad hoc setup with filter=ansible_default_ipv4",
    "ad hoc command which python3 with -vvv"
]

warning = "it skips earlier set_fact so the driver task fails on an undefined variable"

# Let's test widths
for i, it in enumerate(items, 1):
    # monospace factor 0.62, sans factor 0.6
    w_mono_30 = len(it) * 30 * 0.62
    w_sans_30 = len(it) * 30 * 0.60
    print(f"Item {i}: len={len(it):2d} | 30px mono={w_mono_30:6.1f}px, sans={w_sans_30:6.1f}px | '{it}'")
