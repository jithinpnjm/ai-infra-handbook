#!/usr/bin/env python3
"""Self-checking lab for chapter 8.11: monitoring rules from Administrator Manual chapter 10 and appendix G, tested in bcm_monitor.py."""
import sys
import bcm_monitor as m

ok_count = fail_count = 0

def check(name, cond, detail=""):
    global ok_count, fail_count
    ok_count += bool(cond); fail_count += (not cond)
    print(f"{'PASS' if cond else 'FAIL'}  {name}" + (f"   [{detail}]" if detail and not cond else ""))

def raises(fn):
    try:
        fn(); return False
    except m.MonError:
        return True

def main():
    check("health check states: PASS, FAIL, UNKNOWN and no data", m.HEALTH_STATES == ("PASS", "FAIL", "UNKNOWN", "no data"))
    check("default severities: FAIL 15, UNKNOWN 10, PASS 0", [m.severity_for(s) for s in ("FAIL", "UNKNOWN", "PASS")] == [15, 10, 0])
    check("a standalone script can override: 'FAIL 40' gives 40 for FAIL", m.severity_for("FAIL", "FAIL 40") == 40 and m.severity_for("UNKNOWN", "UNKNOWN 10") == 10)
    check("an override for another state does not apply", m.severity_for("FAIL", "UNKNOWN 99") == 15)
    check("no data has no severity", raises(lambda: m.severity_for("no data")))
    t = m.trigger_default_templates()
    check("three default triggers, all with Enter actions, severities 15, 0, 10", t["Failing health checks"]["severity"] == 15 and t["Passing health checks"]["severity"] == 0 and t["Unknown health checks"]["severity"] == 10 and all(v["launch"] == "enter" for v in t.values()))

    a = m.alert_levels({"node001:diskspace": 15, "node002:ssh2node": 10, "node003:mounts": 0})
    check("AlertLevel: count 2 (events at notice level or above), max 15, sum 25", a == {"count": 2, "max": 15, "sum": 25}, a)
    check("AlertLevel with no events is all zero", m.alert_levels({}) == {"count": 0, "max": 0, "sum": 0})

    # triggers: the basic example
    s = [10, 12, 90, 95, 95, 20, 11]
    ev = m.evaluate_trigger(s, ">", 50)
    check("CPUUser > 50: enter at sample 2, during at 3 and 4, leave at 5", ev == [(2, "enter"), (3, "during"), (4, "during"), (5, "leave")], ev)
    check("the first sample can never enter, even if it is already in the zone (no previous sample)", m.evaluate_trigger([90, 95], ">", 50) == [(1, "during")])
    check("the sample right after an enter is 'during', not another enter", [e for _, e in m.evaluate_trigger([10, 90, 91], ">", 50)] == ["enter", "during"])
    check("a drop below the threshold is a leave only if the previous sample was in the zone", m.evaluate_trigger([10, 20, 30], ">", 50) == [])
    check("the default sampling period is 120 s", m.DEFAULT_SAMPLING_SECONDS == 120)
    flap = [10, 90, 10, 90, 10, 90, 10]
    ev = m.evaluate_trigger(flap, ">", 50, interval=10)
    check("flapping: 5 crossings within 5 minutes at a 10 s interval is detected", any(e == "flapping" for _, e in ev), ev)
    ev = m.evaluate_trigger(flap, ">", 50, interval=120)
    check("the same pattern at the default 120 s interval spans 12 minutes: no flapping", not any(e == "flapping" for _, e in ev))
    check("with 120 s sampling at most 2 crossings fit in 5 minutes, so default flap settings can never fire (my arithmetic)", m.max_crossings_in_period(120, 300) == 2 and not m.flapping_detectable())
    check("with 30 s sampling flapping is possible", m.flapping_detectable(interval=30))

    check("validate warns about a measurable name that does not exist (devicestate vs devicestatus)", m.validate_expression("devicestate", ["DeviceStatus", "CPUUser"]) and not m.validate_expression("devicestatus", ["DeviceStatus", "CPUUser"]))
    check("actions: Drain runs on the head (Active) while Reboot runs on the node", m.ACTIONS["Drain"] == "Active" and m.ACTIONS["Reboot"] == "Node")
    check("hard power actions go through BMC or PDU; Reboot and Shutdown are clean", m.HARD_POWER == {"PowerOff", "PowerOn", "PowerReset"} and "Reboot" not in m.HARD_POWER)
    check("an action succeeds with exit code 0", m.action_exit_ok(0) and not m.action_exit_ok(1))

    check("hour consolidator: 65536 samples at 1 h is about 7.5 years (the manual shows 7y 26w)", 7.4 < m.consolidator_retention_years(1, 65536) < 7.6)
    check("doubling maximal samples doubles retention", abs(m.consolidator_retention_years(1, 131072) / m.consolidator_retention_years(1, 65536) - 2) < 1e-9)
    check("scale advice: 500 nodes fine, 15,000 consider offload, 30,000 offload", "fine" in m.monitoring_scale_advice(500) and "consider" in m.monitoring_scale_advice(15000) and m.monitoring_scale_advice(30000) == "use offloaded monitoring")

    check("fourteen GPU health checks are listed", len(m.GPU_HEALTH_CHECKS) == 14)
    check("gpu_health_overall:gpu0 is one GPU, gpu_health_overall alone is all GPUs", m.gpu_check_name("gpu_health_overall", 0) == "gpu_health_overall:gpu0" and m.gpu_check_name("gpu_health_overall") == "gpu_health_overall")
    check("the host engine check takes no GPU", raises(lambda: m.gpu_check_name("gpu_health_hostengine", 0)) and m.gpu_check_name("gpu_health_hostengine") == "gpu_health_hostengine")
    check("an unknown GPU health check is refused", raises(lambda: m.gpu_check_name("gpu_health_fan")))
    check("a DCGM WARN is reported as PASS by default", m.dcgm_result("WARN") == "PASS")
    check("with 'Warn as fail' a DCGM WARN becomes FAIL", m.dcgm_result("WARN", warn_as_fail=True) == "FAIL")
    check("PASS, FAIL and UNKNOWN pass through unchanged", [m.dcgm_result(x) for x in ("PASS", "FAIL", "UNKNOWN")] == ["PASS", "FAIL", "UNKNOWN"])

    check("remediation tier 1 (hardware): drain, notify, evidence, and no automatic reboot or image update", m.remediation_chain("hardware") == ["Drain", "Send e-mail to administrators", "NVSMHealthDump (evidence)"] and "Reboot" not in m.remediation_chain("hardware") and "ImageUpdate" not in m.remediation_chain("hardware"))
    check("remediation tier 2 (software): drain, ImageUpdate, re-check, undrain on PASS", m.remediation_chain("software") == ["Drain", "ImageUpdate", "re-run the health check", "Undrain (on PASS)"])
    check("after the second failed reimage the node moves to tier 1 handling (the loop cap)", m.remediation_chain("software", 2) == m.remediation_chain("hardware"))
    check("tier 3 (transient) does not drain at once", "drain only if it persists" in m.remediation_chain("transient")[-1])
    check("an unknown fault class is refused", raises(lambda: m.remediation_chain("cosmic")))

    print(f"\n{ok_count} passed, {fail_count} failed")
    return 1 if fail_count else 0

if __name__ == "__main__":
    sys.exit(main())
