import re

# Expected 24 labels
expected_labels = [
    "Timer triggers: calendar time versus time since an event",
    "Realtime (calendar): OnCalendar=",
    "OnCalendar=Sun *-*-* 03:00:00",
    "DayOfWeek",
    "Year-Month-Day",
    "Hour:Minute:Second",
    "* wildcard",
    "Mon,Fri list",
    "Mon..Fri range",
    "*:0/15 every 15 minutes",
    "hourly daily weekly monthly yearly",
    'systemd-analyze calendar "Mon..Fri 02:30" prints the normalised form and next elapse times; --iterations=5 shows more',
    "Monotonic: counts from an event",
    "boot",
    "OnBootSec=",
    "unit last activated",
    "OnUnitActiveSec=",
    "every N minutes since the last run",
    "OnStartupSec=, OnUnitInactiveSec=, OnActiveSec=",
    "Persistent=true: remembers the last run on disk and runs a missed job at next start",
    "RandomizedDelaySec=: spreads load across machines",
    "AccuracySec= defaults to one minute so wake-ups combine; set 1s for precision",
    "Enable the timer, not the service: systemctl enable --now fstrim-data.timer; an overlapping oneshot trigger is skipped",
    "Check the zone: add UTC or a zone name when it matters"
]

print(f"Total labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. ({len(l):3d} chars) {l}")
