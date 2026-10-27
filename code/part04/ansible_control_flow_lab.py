#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.8: Ansible handlers, conditionals, loops, blocks and error handling."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_control_flow import (
    FilterModule,
    simulate_block_rescue_always_maintenance,
    simulate_handler_listen_and_failure_loss,
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
    # 1. AUR Ch. 10 Example 10-11 FilterModule.surround_by_quotes
    fm = FilterModule()
    quoted = fm.filters()["surround_by_quotes"](["www.example.com", "example.com"])
    check(
        "FilterModule.surround_by_quotes formats ['www.example.com', 'example.com'] as ['\"www.example.com\"', '\"example.com\"']",
        quoted == ['"www.example.com"', '"example.com"'],
    )

    # 2. Section 1 & AUR Ch. 11 Handler `listen` topic fan-out and lost-handler-on-failure vs force_handlers
    lost = simulate_handler_listen_and_failure_loss(
        config_changed_run1=True,
        later_task_failed_run1=True,
        force_handlers=False,
    )
    forced = simulate_handler_listen_and_failure_loss(
        config_changed_run1=True,
        later_task_failed_run1=True,
        force_handlers=True,
    )
    check(
        "Without force_handlers, a failure after config change skips handlers on both Run 1 and Run 2; force_handlers runs all 3 listen handlers",
        lost["run1_handlers"] == []
        and lost["run2_handlers"] == []
        and forced["run1_handlers"] == ["check_nginx_config", "restart_nginx", "after_config_check"],
    )

    # 3. Section 4 & 6 block/rescue/always GPU maintenance (success resumes node; failure rolls back, runs always, and leaves node DRAINED)
    ok_flow = simulate_block_rescue_always_maintenance(upgrade_succeeds=True, validate_succeeds=True)
    fail_flow = simulate_block_rescue_always_maintenance(upgrade_succeeds=True, validate_succeeds=False, reraise_in_rescue=True)
    check(
        "block/rescue/always resumes healthy node, and on validation failure rolls back, runs always diagnostics, and leaves node DRAINED",
        ok_flow["node_state"] == "RESUMED"
        and ok_flow["host_failed"] is False
        and "always:collect_diagnostics" in ok_flow["events"]
        and fail_flow["node_state"] == "DRAINED"
        and fail_flow["host_failed"] is True
        and "rescue:rollback(validate failed)" in fail_flow["events"]
        and "always:collect_diagnostics" in fail_flow["events"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
