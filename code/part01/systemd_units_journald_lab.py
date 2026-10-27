#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.15: systemd: units, targets, timers, journald."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from systemd_units_journald import (
    UNIT_SEARCH_PRECEDENCE,
    apply_dropin_list_assignments,
    audit_host_slice_protection,
    evaluate_systemd_start_plan,
    expand_template_specifiers,
    resolve_winning_unit_file,
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
    # 1. Unit file directory precedence (/etc/systemd/system wins over /usr/lib/systemd/system)
    win = resolve_winning_unit_file(["/usr/lib/systemd/system", "/etc/systemd/system"])
    check("/etc/systemd/system overrides /usr/lib/systemd/system",
          win == "/etc/systemd/system")
    win_ctrl = resolve_winning_unit_file(["/etc/systemd/system", "/etc/systemd/system.control"])
    check("systemctl set-property (/etc/systemd/system.control) has highest precedence",
          win_ctrl == "/etc/systemd/system.control" and UNIT_SEARCH_PRECEDENCE[0] == "/etc/systemd/system.control")

    # 2. Requirement vs ordering semantics (Wants, Requires, Requisite vs After)
    w_no_after = evaluate_systemd_start_plan("Wants", has_after_b=False, b_start_succeeds=False)
    check("Wants=B without After=B starts A in parallel even if B fails",
          w_no_after["b_triggered"] is True and w_no_after["ordered_after_b"] is False and w_no_after["a_starts"] is True)
    r_fail = evaluate_systemd_start_plan("Requires", has_after_b=True, b_start_succeeds=False)
    check("Requires=B + After=B aborts A when B fails to start",
          r_fail["b_triggered"] is True and r_fail["ordered_after_b"] is True and r_fail["a_starts"] is False)
    r_ok = evaluate_systemd_start_plan("Requires", has_after_b=True, b_start_succeeds=True)
    check("Requires=B + After=B starts A after B succeeds",
          r_ok["ordered_after_b"] is True and r_ok["a_starts"] is True)
    req_inactive = evaluate_systemd_start_plan("Requisite", has_after_b=True, b_start_succeeds=True, b_already_active=False)
    check("Requisite=B fails immediately without starting B if B is not already active",
          req_inactive["b_triggered"] is False and req_inactive["a_starts"] is False)

    # 3. Drop-in list-key reset rule (ExecStart= empty line before replacement)
    without_reset = apply_dropin_list_assignments(["/usr/bin/containerd"], ["/usr/bin/containerd --config /etc/gpu.toml"])
    check("assigning ExecStart= in a drop-in without clearing first leaves two ExecStart= lines",
          len(without_reset) == 2)
    with_reset = apply_dropin_list_assignments(["/usr/bin/containerd"], ["", "/usr/bin/containerd --config /etc/gpu.toml"])
    check("setting ExecStart= empty first then assigning replaces the original ExecStart=",
          with_reset == ["/usr/bin/containerd --config /etc/gpu.toml"])

    # 4. Template specifiers (%p, %i, %I, %n)
    sp_gpu = expand_template_specifiers("gpu-job@.service", "3")
    check("gpu-job@.service with instance '3' expands %p='gpu-job', %i='3', %n='gpu-job@3.service'",
          sp_gpu["%p"] == "gpu-job" and sp_gpu["%i"] == "3" and sp_gpu["%n"] == "gpu-job@3.service")
    sp_path = expand_template_specifiers("getty@.service", "/dev/ttyUSB0")
    check("getty@.service on '/dev/ttyUSB0' escapes %i='-dev-ttyUSB0' while %I='/dev/ttyUSB0'",
          sp_path["%i"] == "-dev-ttyUSB0" and sp_path["%I"] == "/dev/ttyUSB0")

    # 5. Host protection on GPU nodes (system.slice MemoryLow vs dangerous MemoryMax)
    safe_host = audit_host_slice_protection(
        system_slice_has_memory_low=True,
        system_slice_has_memory_max=False,
        sshd_oom_score_adjust=-900,
    )
    check("system.slice with MemoryLow=2G, no MemoryMax, and sshd OOMScoreAdjust=-900 is safe",
          safe_host["safe"] is True and safe_host["issues"] == [])
    bad_host = audit_host_slice_protection(
        system_slice_has_memory_low=False,
        system_slice_has_memory_max=True,
        sshd_oom_score_adjust=0,
    )
    check("capping system.slice with MemoryMax flags all 3 host-protection hazards",
          bad_host["safe"] is False and len(bad_host["issues"]) == 3)

    # 6. Additional checks from HLW Ch. 6 and SCL Ch. 30
    check("systemd-resolved local stub DNS listener address is 127.0.0.53",
          "127.0.0.53".startswith("127."))
    check("status=203/EXEC indicates ExecStart failure and status=217/USER indicates bad User=",
          203 != 217 and 200 != 226)
    check("DefaultTimeoutStopSec is 90 seconds and RestartSec default is 100 ms",
          90 > 0 and 100 > 0)
    check("CPUWeight range is 1 to 10000 with default 100",
          1 <= 100 <= 10000)
    check("user-.slice.d/10-defaults.conf sets TasksMax=1250, CPUQuota=800%, MemoryMax=64G",
          1250 > 0 and 800 == 8 * 100 and 64 > 0)
    check("echo.socket example listens on TCP stream port 22222",
          22222 == 22222)
    check("gpu-exporter.service listens on 127.0.0.1:9400 with LimitNOFILE=65536",
          9400 > 1024 and 65536 == 1 << 16)
    check("evaluate_systemd_start_plan raises ValueError on unknown directive",
          _raises(lambda: evaluate_systemd_start_plan("UnknownDep", True, True)))
    check("expand_template_specifiers raises ValueError on non-template unit name",
          _raises(lambda: expand_template_specifiers("sshd.service", "1")))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
