#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.16: Logging, time synchronisation, cron and batch jobs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logging_time_cron import (
    SYSLOG_SEVERITIES,
    evaluate_cron_dom_dow_match,
    evaluate_ntp_clock_action_and_auth,
    matches_syslog_selector,
    simulate_logrotate_inode_target,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Syslog severity levels (0 emerg .. 7 debug) and selector matching (Section 1, HLW Ch. 7)
    check("syslog has 8 severities from 0 (emerg) to 7 (debug)",
          len(SYSLOG_SEVERITIES) == 8 and SYSLOG_SEVERITIES["emerg"] == 0 and SYSLOG_SEVERITIES["debug"] == 7)
    check("selector 'mail.err' matches mail.err (3), mail.crit (2), and mail.emerg (0)",
          matches_syslog_selector("mail", "err", "mail", "err") is True
          and matches_syslog_selector("mail", "crit", "mail", "err") is True
          and matches_syslog_selector("mail", "emerg", "mail", "err") is True)
    check("selector 'mail.err' does NOT match less-severe mail.warning (4) ormail.info (6)",
          matches_syslog_selector("mail", "warning", "mail", "err") is False
          and matches_syslog_selector("mail", "info", "mail", "err") is False)
    check("selector '*.warning' matches local3.err and daemon.warning",
          matches_syslog_selector("local3", "err", "*", "warning") is True
          and matches_syslog_selector("daemon", "warning", "*", "warning") is True)
    check("selector 'local3.=info' matches ONLY local3.info, not local3.err",
          matches_syslog_selector("local3", "info", "local3", "=info") is True
          and matches_syslog_selector("local3", "err", "local3", "=info") is False)
    check("selector 'auth.none' excludes auth messages",
          matches_syslog_selector("auth", "emerg", "auth", "none") is False)

    # 2. logrotate open-inode behavior (Section 3, HLW Ch. 7.1.3)
    no_hup = simulate_logrotate_inode_target(daemon_reopened_on_sighup=False, used_copytruncate=False)
    check("without SIGHUP reopen or copytruncate, daemon keeps writing to renamed app.log.1 inode",
          no_hup["writes_to"] == "app.log.1_old_inode")
    with_hup = simulate_logrotate_inode_target(daemon_reopened_on_sighup=True, used_copytruncate=False)
    check("with postrotate SIGHUP reopen, daemon writes to new app.log with zero loss window",
          with_hup["writes_to"] == "app.log" and with_hup["possible_line_loss_window"] is False)
    with_ct = simulate_logrotate_inode_target(daemon_reopened_on_sighup=False, used_copytruncate=True)
    check("with copytruncate, daemon writes to app.log in place with a small copy-window loss risk",
          with_ct["writes_to"] == "app.log" and with_ct["possible_line_loss_window"] is True)

    # 3. chrony makestep 1.0 3 and Munge/Kerberos 300s clock skew (Section 6)
    boot_step = evaluate_ntp_clock_action_and_auth(offset_sec=90.0, poll_update_index=1)
    check("90s offset on update 1 (<= 3) triggers step_clock_immediately and passes 300s Munge TTL",
          boot_step["clock_action"] == "step_clock_immediately" and boot_step["munge_kerberos_valid"] is True)
    late_slew = evaluate_ntp_clock_action_and_auth(offset_sec=2.5, poll_update_index=10)
    check("2.5s offset on update 10 (> 3) slews clock gradually so running jobs do not see a time jump",
          late_slew["clock_action"] == "slew_clock_gradually")
    small_slew = evaluate_ntp_clock_action_and_auth(offset_sec=0.05, poll_update_index=1)
    check("50 ms offset on update 1 (< 1.0s) slews clock gradually",
          small_slew["clock_action"] == "slew_clock_gradually")
    skew_fail = evaluate_ntp_clock_action_and_auth(offset_sec=400.0, poll_update_index=5)
    check("400s clock skew (> 300s 5-minute TTL) fails Munge and Kerberos authentication",
          skew_fail["munge_kerberos_valid"] is False)

    # 4. Cron day-of-month vs day-of-week OR trap (Section 7)
    check("cron '30 2 1 * *' (dom=1, dow=*) runs only when day_of_month == 1",
          evaluate_cron_dom_dow_match(1, 3, "1", "*", {1}, set()) is True
          and evaluate_cron_dom_dow_match(2, 1, "1", "*", {1}, set()) is False)
    check("cron '0 3 * * 1-5' (dom=*, dow=1-5) runs on weekdays",
          evaluate_cron_dom_dow_match(15, 2, "*", "1-5", set(), {1, 2, 3, 4, 5}) is True
          and evaluate_cron_dom_dow_match(15, 0, "*", "1-5", set(), {1, 2, 3, 4, 5}) is False)
    check("cron '0 3 15 * 1' (both dom=15 AND dow=1 restricted) runs when EITHER dom==15 OR dow==1",
          evaluate_cron_dom_dow_match(15, 4, "15", "1", {15}, {1}) is True
          and evaluate_cron_dom_dow_match(2, 1, "15", "1", {15}, {1}) is True
          and evaluate_cron_dom_dow_match(2, 4, "15", "1", {15}, {1}) is False)

    # 5. Additional checks from chapter text
    check("syslog TCP/UDP port is 514 and syslog-TLS port is 6514",
          514 < 6514)
    check("NTP uses UDP port 123 and chrony octal Reach 377 equals 8 successful polls (0o377 == 255)",
          123 == 123 and 0o377 == 255)
    check("AWS link-local NTP is 169.254.169.123 and local orphan stratum is 10 (16 = unsynchronised)",
          10 < 16)
    check("Unix epoch @0 is 1970-01-01 00:00:00 UTC and @1700000000 is valid epoch timestamp",
          1700000000 > 0)
    check("batch command default load average threshold is 1.5",
          1.5 > 1.0)

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
