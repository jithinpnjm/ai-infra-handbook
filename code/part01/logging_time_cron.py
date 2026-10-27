"""Chapter 1.16 model: Syslog facility and severity (0 emerg .. 7 debug) rule
matching, logrotate open-inode behavior (SIGHUP reopen vs copytruncate), NTP
slew vs makestep threshold and Munge/Kerberos 300s clock-skew check, and 5-field
cron expression evaluation (including the day-of-month OR day-of-week rule).

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 7
  ("System Configuration: Logging, System Time, Batch Jobs, and Users": sections
  7.1 syslog/journald/logrotate, 7.4 getty/login, 7.5 RTC hwclock/adjtimex/UTC/NTP,
  7.6 cron vs systemd timers, 7.7 at and systemd-run, 7.8 user timers and linger).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 7 and
  Chapter 28 (NTP server and compute-node configuration).
"""
from typing import Dict, List, Set


SYSLOG_SEVERITIES: Dict[str, int] = {
    "emerg": 0,
    "alert": 1,
    "crit": 2,
    "err": 3,
    "warning": 4,
    "notice": 5,
    "info": 6,
    "debug": 7,
}


def matches_syslog_selector(
    msg_facility: str,
    msg_severity: str,
    rule_facility: str,
    rule_severity_spec: str,
) -> bool:
    """Evaluate a classic syslog selector (e.g. 'mail.err', '*.warning', 'local3.=info')."""
    if rule_facility != "*" and rule_facility != msg_facility:
        return False
    if rule_severity_spec == "none":
        return False
    if rule_severity_spec == "*":
        return True
    msg_lvl = SYSLOG_SEVERITIES[msg_severity]
    if rule_severity_spec.startswith("="):
        target_lvl = SYSLOG_SEVERITIES[rule_severity_spec[1:]]
        return msg_lvl == target_lvl
    target_lvl = SYSLOG_SEVERITIES[rule_severity_spec]
    return msg_lvl <= target_lvl  # lower number = more severe


def simulate_logrotate_inode_target(
    daemon_reopened_on_sighup: bool,
    used_copytruncate: bool,
) -> Dict[str, object]:
    """Model where a daemon writes after logrotate renames 'app.log' to 'app.log.1'."""
    if used_copytruncate:
        return {"writes_to": "app.log", "possible_line_loss_window": True}
    if daemon_reopened_on_sighup:
        return {"writes_to": "app.log", "possible_line_loss_window": False}
    return {"writes_to": "app.log.1_old_inode", "possible_line_loss_window": False}


def evaluate_ntp_clock_action_and_auth(
    offset_sec: float,
    poll_update_index: int,
    makestep_threshold_sec: float = 1.0,
    makestep_limit_updates: int = 3,
    munge_ttl_sec: float = 300.0,
) -> Dict[str, object]:
    """Determine whether chrony steps or slews the clock (makestep 1.0 3) and whether Munge/Kerberos accepts credentials."""
    abs_off = abs(offset_sec)
    if abs_off > makestep_threshold_sec and (makestep_limit_updates < 0 or poll_update_index <= makestep_limit_updates):
        clock_action = "step_clock_immediately"
    else:
        clock_action = "slew_clock_gradually"
    return {
        "abs_offset_sec": abs_off,
        "clock_action": clock_action,
        "munge_kerberos_valid": abs_off <= munge_ttl_sec,
    }


def evaluate_cron_dom_dow_match(
    day_of_month: int,
    day_of_week: int,
    dom_field: str,
    dow_field: str,
    dom_matches: Set[int],
    dow_matches: Set[int],
) -> bool:
    """Model POSIX cron's OR rule when both day-of-month (field 3) and day-of-week (field 5) are restricted (not '*')."""
    dom_is_star = dom_field.strip() == "*"
    dow_is_star = dow_field.strip() == "*"
    if dom_is_star and dow_is_star:
        return True
    if dom_is_star:
        return day_of_week in dow_matches
    if dow_is_star:
        return day_of_month in dom_matches
    # Both restricted: matches if EITHER day_of_month OR day_of_week matches!
    return (day_of_month in dom_matches) or (day_of_week in dow_matches)
