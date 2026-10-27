#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.6: Ansible playbooks: tasks, modules, idempotency and check mode."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_playbook_execution import (
    compute_serial_batches,
    evaluate_command_task_guards,
    simulate_play_execution_and_handlers,
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
    # 1. Section 1 & AUR Ch. 3: Play phase order and handler deduplication (3 tasks notify 'Restart nginx' -> runs once)
    log = simulate_play_execution_and_handlers(
        pre_tasks=[("assert_os", False, "")],
        role_tasks=[("install_nginx", True, "")],
        main_tasks=[
            ("copy_tls_certs", True, "Restart nginx"),
            ("render_nginx_conf", True, "Restart nginx"),
            ("enable_site_symlink", True, "Restart nginx"),
        ],
        post_tasks=[("uri_smoke_test", False, "")],
    )
    check(
        "Play runs pre_tasks -> roles -> tasks -> deduplicated handler 'Restart nginx' (once) -> post_tasks",
        log
        == [
            "task:assert_os:ok",
            "task:install_nginx:changed",
            "task:copy_tls_certs:changed",
            "task:render_nginx_conf:changed",
            "task:enable_site_symlink:changed",
            "handler:Restart nginx",
            "task:uri_smoke_test:ok",
        ],
    )

    # 2. Section 2, 4, 5: command/shell guards (creates, --check vs check_mode: false, changed_when: false)
    skip_creates = evaluate_command_task_guards(existing_paths={"/scratch"}, creates="/scratch")
    skip_check = evaluate_command_task_guards(existing_paths=set(), in_check_mode=True)
    probe_check = evaluate_command_task_guards(
        existing_paths=set(),
        in_check_mode=True,
        task_check_mode_override=False,
        simulated_stdout="8",
        changed_when_expr="false",
    )
    check(
        "creates='/scratch' skips when present, unguarded command skips in --check, and check_mode:false + changed_when:false runs probe cleanly",
        skip_creates["skipped"] is True
        and skip_check["skipped"] is True
        and probe_check["skipped"] is False
        and probe_check["changed"] is False,
    )

    # 3. Section 6 & 7: Progressive serial batching `serial: [1, '20%', '100%']` over 10 GPU hosts
    hosts = [f"gpu{i:02d}" for i in range(1, 11)]
    batches = compute_serial_batches(hosts, [1, "20%", "100%"])
    check(
        "serial: [1, '20%', '100%'] over 10 hosts creates canary [gpu01], 20% batch [gpu02, gpu03], and remaining 7 hosts",
        batches == [["gpu01"], ["gpu02", "gpu03"], ["gpu04", "gpu05", "gpu06", "gpu07", "gpu08", "gpu09", "gpu10"]],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
