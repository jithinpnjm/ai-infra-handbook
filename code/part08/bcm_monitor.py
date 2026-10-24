#!/usr/bin/env python3
"""BCM monitoring rules from the Administrator Manual chapter 10 and appendix G (and the NVIDIA-DevOps notes, volume 10 chapter 13), as testable pieces.

Not BCM. Each part names the manual section it follows; things that are my reading or a design recommendation are labelled as such.
"""
import math, operator, re

class MonError(ValueError):
    pass

# ---- 10.2.4 health checks --------------------------------------------------------------------------------------------
HEALTH_STATES = ("PASS", "FAIL", "UNKNOWN", "no data")
DEFAULT_SEVERITY = {"FAIL": 15, "UNKNOWN": 10, "PASS": 0}

def severity_for(state, script_override=None):
    """Default severities: FAIL 15, UNKNOWN 10, PASS 0 (trigger templates). A standalone health check script can override it with its own value,
    for example 'FAIL 40' (the hpraid script)."""
    if state not in DEFAULT_SEVERITY:
        raise MonError("severity applies to PASS, FAIL and UNKNOWN")
    if script_override:
        m = re.fullmatch(r"(PASS|FAIL|UNKNOWN)\s+(\d+)", script_override.strip())
        if m and m.group(1) == state:
            return int(m.group(2))
    return DEFAULT_SEVERITY[state]

def alert_levels(latest_severities, notice=10):
    """AlertLevel: count = number of events at notice level and higher; max = highest latest severity; sum = sum of the latest severities.
    The numeric value of 'notice' is my reading (10); the manual's table is garbled in the text I had."""
    vals = list(latest_severities.values())
    return {"count": sum(1 for v in vals if v >= notice), "max": max(vals, default=0), "sum": sum(vals)}

# ---- 10.1, 10.4.5 triggers ----------------------------------------------------------------------------------------------
OPS = {">": operator.gt, "<": operator.lt, ">=": operator.ge, "<=": operator.le, "==": operator.eq, "eq": operator.eq, "!=": operator.ne}
DEFAULT_SAMPLING_SECONDS = 120
FLAP_COUNT, FLAP_PERIOD = 5, 300

def evaluate_trigger(samples, op, threshold, interval=DEFAULT_SAMPLING_SECONDS, flap_count=FLAP_COUNT, flap_period=FLAP_PERIOD):
    """Returns [(sample_index, 'enter'|'leave'|'during'|'flapping')].
      enter   sample in the zone and the PREVIOUS sample not in the zone (so the first sample can never 'enter': there is no previous sample)
      leave   sample not in the zone and the previous sample in it
      during  sample in the zone and the previous sample also in it
      flapping  at least flap_count threshold crossings (enters+leaves) within flap_period seconds"""
    f = OPS[op]
    events, crossings = [], []
    prev = None
    for i, v in enumerate(samples):
        inz = f(v, threshold)
        if prev is not None:
            if inz and not prev:
                events.append((i, "enter")); crossings.append(i * interval)
            elif not inz and prev:
                events.append((i, "leave")); crossings.append(i * interval)
            elif inz and prev:
                events.append((i, "during"))
            recent = [t for t in crossings if t > i * interval - flap_period]
            if len(recent) >= flap_count and (not events or events[-1][1] != "flapping"):
                events.append((i, "flapping"))
        prev = inz
    return events

def max_crossings_in_period(interval, period):
    """My reading: crossings are seen only between consecutive samples, so within `period` seconds at most about period/interval of them can be seen."""
    return int(period // interval)

def flapping_detectable(interval=DEFAULT_SAMPLING_SECONDS, flap_count=FLAP_COUNT, flap_period=FLAP_PERIOD):
    """With the default 120 s sampling and the default flap setting (5 crossings in 5 minutes) flapping cannot be seen on that measurable: at most 2
    crossings fit in 300 s. This is my arithmetic from the manual's defaults, not a statement in the manual."""
    return max_crossings_in_period(interval, flap_period) >= flap_count

def validate_expression(measurable_regex, known_measurables):
    """cmsh `validate` warns when no known measurable matches the regex (the manual's devicestate vs devicestatus example) and when no actions are set."""
    p = []
    if not any(re.fullmatch(measurable_regex, m, re.I) for m in known_measurables):
        p.append(f"Warning: No known measurable matches the specified regexes ('{measurable_regex}', '')")
    return p

ACTIONS = {"Drain": "Active", "Undrain": "Active", "Send e-mail to administrators": "Active", "Event": "Active", "ImageUpdate": "Active",
           "PowerOff": "Active", "PowerOn": "Active", "PowerReset": "Active", "Reboot": "Node", "Shutdown": "Node",
           "killprocess": "Node", "remount": "Node", "testaction": "Node"}
HARD_POWER = {"PowerOff", "PowerOn", "PowerReset"}     # through the BMC or PDU; Reboot and Shutdown are clean, through the system

def action_exit_ok(exit_code):
    """An action is a script or built-in that exits 0 on success."""
    return exit_code == 0

def trigger_default_templates():
    return {"Failing health checks": {"launch": "enter", "severity": 15}, "Passing health checks": {"launch": "enter", "severity": 0},
            "Unknown health checks": {"launch": "enter", "severity": 10}}

# ---- 10.5.2 consolidation --------------------------------------------------------------------------------------------------
def consolidator_retention_years(interval_hours, max_samples):
    """The default 'hour' consolidator keeps at most 65536 averaged samples at 1 h: about 7.5 years (the manual shows period 7y 26w)."""
    return interval_hours * max_samples / 24 / 365.25

# ---- 10.7 offload ---------------------------------------------------------------------------------------------------------------
def monitoring_scale_advice(nodes):
    """Manual: the traditional design copes with about 10,000 nodes with default metrics; a limit was reached around 20,000 nodes on 2020 hardware.
    Offloaded monitoring (the `monitoring` role on nodes) removes the head node as single point of failure and scales with the cluster."""
    if nodes < 10000:
        return "traditional monitoring on the head node is fine"
    if nodes < 20000:
        return "traditional monitoring is near its comfortable limit: consider offloaded monitoring"
    return "use offloaded monitoring"

# ---- G.2.2 GPU health checks ------------------------------------------------------------------------------------------------------
GPU_HEALTH_CHECKS = ["gpu_health_driver", "gpu_health_hostengine", "gpu_health_inforom", "gpu_health_mcu", "gpu_health_mem", "gpu_health_nvlink",
                     "gpu_health_nvswitch_fatal", "gpu_health_nvswitch_non_fatal", "gpu_health_overall", "gpu_health_pcie", "gpu_health_pmu",
                     "gpu_health_power", "gpu_health_sm", "gpu_health_thermal"]
NO_GPU_PARAMETER = {"gpu_health_hostengine"}        # the host engine check is for all GPUs on the node

def gpu_check_name(check, gpu=None):
    if check not in GPU_HEALTH_CHECKS:
        raise MonError(f"unknown GPU health check {check}")
    if check in NO_GPU_PARAMETER and gpu is not None:
        raise MonError(f"{check} is specified without a GPU: it checks all GPUs on the node")
    return check if gpu is None else f"{check}:gpu{gpu}"

def dcgm_result(dcgm, warn_as_fail=False):
    """A DCGM WARN does not add a fourth state: it is reported as PASS (reason in the Info field) unless the GPUSampler extra parameter 'Warn as fail' is true."""
    if dcgm == "WARN":
        return "FAIL" if warn_as_fail else "PASS"
    if dcgm in ("PASS", "FAIL", "UNKNOWN"):
        return dcgm
    raise MonError("DCGM results are PASS, WARN, FAIL or UNKNOWN")

# ---- remediation (the notes' design recommendation, NOT a BCM feature) --------------------------------------------------------
def remediation_chain(fault_class, reimages_so_far=0):
    """Design recommendation from the notes (volume 10 chapter 13): tier 1 suspected hardware fault: drain, notify, collect evidence, no automatic reboot or
    image update. Tier 2 reproducible software state: drain, ImageUpdate (or reboot), re-check, undrain on PASS; cap the loop and move to tier 1 handling after
    the second failure. Tier 3 transient: alert, use flapping and UNKNOWN handling, drain only if it persists."""
    if fault_class == "hardware":
        return ["Drain", "Send e-mail to administrators", "NVSMHealthDump (evidence)"]
    if fault_class == "software":
        if reimages_so_far >= 2:
            return remediation_chain("hardware")
        return ["Drain", "ImageUpdate", "re-run the health check", "Undrain (on PASS)"]
    if fault_class == "transient":
        return ["Event", "Send e-mail to administrators (drain only if it persists)"]
    raise MonError("fault class is hardware, software or transient")
