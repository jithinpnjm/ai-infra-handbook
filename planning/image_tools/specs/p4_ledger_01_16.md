# docs/part-01-linux/16-logging-time-synchronisation-cron-and-batch-jobs.md
- ## Why this matters for AI infrastructure | 310 words | NO FIGURE NEEDED: motivational overview connecting logging, clock synchronisation, and cron to cluster reliability
- ## Prerequisites and outcomes | 200 words | NO FIGURE NEEDED: prerequisite checklist and learning outcomes
- ## 1. System logging | 380 words | NEEDS FIGURE: host logging ingestion architecture showing /dev/log, service output, kernel messages, journald, and rsyslog forwarding
- ### Checking what your machine runs | 190 words | NO FIGURE NEEDED: inspection command checklist and file paths
- ### rsyslog in a nutshell | 350 words | COVERED(p3-0116-selector-anatomy)
- ### Journal versus syslog | 160 words | COVERED(l16-severity)
- ## 2. Searching and monitoring logs | 450 words | COVERED(p3-0116-journal-field-trust)
- ## 3. Rotating logs | 550 words | COVERED(p3-0116-logrotate-anatomy, l16-rotation-inode)
- ## 4. Central logging for clusters | 420 words | COVERED(ch16-d1-luna)
- ## 5. Final notes on logging | 180 words | NO FIGURE NEEDED: best practices summary on JSON schema, UTC, and trust model
- ## 6. Time | 140 words | COVERED(p3-0116-skew-symptoms)
- ### The clocks | 300 words | COVERED(ch16-d2-luna)
- ### Time zones | 250 words | NO FIGURE NEEDED: configuration via /etc/localtime symlink and TZ environment variable
- ### Network time: NTP | 480 words | COVERED(p3-0116-chronyc-read, p3-0116-ntp-two-tier)
- ### Classic ntpd setup for a small cluster | 120 words | NO FIGURE NEEDED: brief legacy reference recipe
- ## 7. Scheduling recurring tasks: cron | 250 words | COVERED(p3-0116-cron-dom-dow)
- ### Where crontabs live | 170 words | COVERED(p2-0116-cron-user-system)
- ### Cron's environment (the cause of most "works in my shell" failures) | 180 words | COVERED(p3-0116-cron-env-gap)
- ### Making cron jobs safe | 340 words | COVERED(p3-0116-cron-ladder, l16-safe-cron)
- ## 8. One-time tasks: `at`, `batch` and `systemd-run` | 240 words | NO FIGURE NEEDED: syntax and usage comparison for one-off commands
- ## 9. cron versus systemd timers (*How Linux Works* Section 7.6.4) | 330 words | COVERED(p3-0116-cron-vs-timer)
- ## 10. AI-infrastructure patterns | 450 words | COVERED(p3-0116-clock-before-auth)
- ## How it fails | 350 words | NO FIGURE NEEDED: numbered failure mode catalog
- ## Hands-on lab: logging, logrotate, chrony, cron, and VM drills | 450 words | NO FIGURE NEEDED: terminal commands and lab exercises
- ## Exercises | 270 words | NO FIGURE NEEDED: homework problems
- ## Checkpoint questions (20) | 1200 words | NO FIGURE NEEDED: review Q and A cards
- ## Sources and review notes | 250 words | NO FIGURE NEEDED: bibliography and citation notes

Specs kept 1, dropped 0: []
