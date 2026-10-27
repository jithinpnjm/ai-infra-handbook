"""Chapter 1.15 model: systemd unit path precedence (/etc vs /run vs /usr/lib),
dependency vs ordering semantics (Wants/Requires/Requisite/BindsTo vs After/Before),
drop-in list-key reset rules (ExecStart= empty reset), template specifier escaping
(%i vs %I), and slice resource protection (MemoryLow/CPUWeight on system.slice vs
MemoryMax on workload slices).

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 6
  ("How User Space Starts": init implementations systemd/SysV/Upstart/runit/Android,
  units, dependency graphs, systemctl, Type=simple/forking/oneshot/notify/dbus,
  Wants/Requires/Before/After, [Install] WantedBy, socket activation echo.socket,
  SysV /etc/inittab respawn mingetty and /etc/rc5.d S10sysklogd..S99sshd link farm,
  initramfs mkinitramfs/unmkinitramfs and dracut).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 7, Chapter 23,
  and Chapter 30 ("Systemd – A Short Course": unit sections, StandardInput/Output
  tty-force/tty-fail, drop-in overrides, user-UID.slice limits, networkd, resolved,
  timesyncd, journald).
- nvidia-devops/volume-01/04-linux-systemd-containers-masterclass.md (GPU service
  ordering nvidia-fabricmanager -> containerd -> kubelet, system.slice MemoryLow).
"""
from typing import Dict, List, Tuple


UNIT_SEARCH_PRECEDENCE: List[str] = [
    "/etc/systemd/system.control",
    "/run/systemd/transient",
    "/etc/systemd/system",
    "/run/systemd/system",
    "/run/systemd/generator",
    "/usr/lib/systemd/system",
]


def resolve_winning_unit_file(present_in_dirs: List[str]) -> str:
    """Return the winning unit directory given the set of directories containing NAME.service."""
    for d in UNIT_SEARCH_PRECEDENCE:
        if d in present_in_dirs:
            return d
    return "NOT_FOUND"


def evaluate_systemd_start_plan(
    unit_a_dep_type: str,
    has_after_b: bool,
    b_start_succeeds: bool,
    b_already_active: bool = False,
) -> Dict[str, object]:
    """Model whether unit A starts, whether B is triggered, and whether A waits for B to finish starting."""
    if unit_a_dep_type == "Requisite":
        if not b_already_active:
            return {"b_triggered": False, "ordered_after_b": has_after_b, "a_starts": False}
        return {"b_triggered": False, "ordered_after_b": has_after_b, "a_starts": True}
    if unit_a_dep_type == "Wants":
        return {"b_triggered": True, "ordered_after_b": has_after_b, "a_starts": True}
    if unit_a_dep_type in {"Requires", "BindsTo"}:
        return {"b_triggered": True, "ordered_after_b": has_after_b, "a_starts": b_start_succeeds}
    raise ValueError(f"Unsupported dependency directive: {unit_a_dep_type}")


def apply_dropin_list_assignments(base_values: List[str], dropin_values: List[str]) -> List[str]:
    """Apply systemd drop-in rule for list keys (e.g. ExecStart=): an empty string '' clears prior values."""
    result = list(base_values)
    for val in dropin_values:
        if val == "":
            result = []
        else:
            result.append(val)
    return result


def expand_template_specifiers(template_unit: str, raw_instance: str) -> Dict[str, str]:
    """Compute %p (prefix), %i (escaped instance), %I (unescaped path/instance), and %n (full unit name)."""
    if "@." not in template_unit:
        raise ValueError(f"Expected template unit containing '@.', got: {template_unit}")
    prefix, suffix = template_unit.split("@.", 1)
    escaped_i = raw_instance.strip("/").replace("/", "-") if raw_instance.startswith("/") else raw_instance
    if raw_instance.startswith("/"):
        escaped_i = "-" + escaped_i
    return {
        "%p": prefix,
        "%i": escaped_i,
        "%I": raw_instance,
        "%n": f"{prefix}@{escaped_i}.{suffix}",
    }


def audit_host_slice_protection(
    system_slice_has_memory_low: bool,
    system_slice_has_memory_max: bool,
    sshd_oom_score_adjust: int,
) -> Dict[str, object]:
    """Verify host-protection rules from Section 10 (protect system.slice with MemoryLow, never cap it with MemoryMax)."""
    issues: List[str] = []
    if not system_slice_has_memory_low:
        issues.append("missing_MemoryLow_on_system_slice")
    if system_slice_has_memory_max:
        issues.append("dangerous_MemoryMax_on_system_slice_can_kill_sshd_kubelet")
    if sshd_oom_score_adjust > -500:
        issues.append("sshd_oom_score_adjust_not_protected")
    return {"safe": len(issues) == 0, "issues": issues}
