"""Chapter 4.6 model: Playbook execution phase order (`pre_tasks` -> `roles` ->
`tasks` -> `post_tasks` with handler flushes and `notify` deduplication),
`command`/`shell` idempotency guards (`creates`, `removes`, `changed_when`,
`failed_when`, `check_mode`), `serial: [1, '10%', '100%']` batch planner, and
`ansible-playbook` exit-code classification.

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapter 3 ("Playbooks: A Beginning"):
  * Executable playbook shebang (`#!/usr/bin/env ansible-playbook`, `chmod +x`),
    play-level `vars:` (`tls_dir`, `key_file`, `cert_file`, `conf_file`, `server_name`),
    `package` (`name=nginx update_cache=true`), `file` (`state: directory`,
    `state: link` symlink `/etc/nginx/sites-enabled/default -> /etc/nginx/sites-available/default`),
    `copy` with `loop:`, `template` (`nginx.conf.j2`, `index.html.j2`),
    `notify: Restart nginx` handler deduplication (runs once at the end of the
    play even if notified by 3 tasks!), and `uri` smoke-test task (`return_content: true`,
    `register: this`, `failed_when: "'Running on ' not in this.content"`, `tags: [test]`).
"""
import math
from typing import Dict, List, Sequence, Set, Tuple


def simulate_play_execution_and_handlers(
    pre_tasks: Sequence[Tuple[str, bool, str]],
    role_tasks: Sequence[Tuple[str, bool, str]],
    main_tasks: Sequence[Tuple[str, bool, str]],
    post_tasks: Sequence[Tuple[str, bool, str]],
) -> List[str]:
    """Model Section 1 & AUR Ch. 3 play phase execution order:
      pre_tasks -> flush handlers -> roles + tasks -> flush handlers -> post_tasks -> flush handlers.
    Each task is `(task_name, changed, notify_handler_name_or_empty)`.
    Even if multiple tasks notify the same handler within a phase, the handler
    runs ONLY ONCE when flushed, in the order handlers are defined.
    """
    log: List[str] = []
    pending_handlers: List[str] = []

    def _run_phase(phase_tasks: Sequence[Tuple[str, bool, str]]) -> None:
        for t_name, changed, handler in phase_tasks:
            log.append(f"task:{t_name}:{'changed' if changed else 'ok'}")
            if changed and handler and handler not in pending_handlers:
                pending_handlers.append(handler)

    def _flush() -> None:
        while pending_handlers:
            h = pending_handlers.pop(0)
            log.append(f"handler:{h}")

    _run_phase(pre_tasks)
    _flush()
    _run_phase(role_tasks)
    _run_phase(main_tasks)
    _flush()
    _run_phase(post_tasks)
    _flush()
    return log


def evaluate_command_task_guards(
    *,
    existing_paths: Set[str],
    creates: str | None = None,
    removes: str | None = None,
    in_check_mode: bool = False,
    task_check_mode_override: bool | None = None,
    simulated_rc: int = 0,
    simulated_stdout: str = "",
    changed_when_expr: str = "default",
) -> Dict[str, object]:
    """Model Section 2, 4, 5 `command`/`shell` guard evaluation (`creates`,
    `removes`, `--check` mode vs `check_mode: false`, and `changed_when`).
    """
    if creates and creates in existing_paths:
        return {"skipped": True, "changed": False, "reason": f"Did not run command since {creates!r} exists"}
    if removes and removes not in existing_paths:
        return {"skipped": True, "changed": False, "reason": f"Did not run command since {removes!r} does not exist"}

    effective_check = in_check_mode if task_check_mode_override is None else task_check_mode_override
    if effective_check and not creates and not removes:
        return {"skipped": True, "changed": False, "reason": "skipped in check mode"}

    if changed_when_expr == "false":
        changed = False
    elif changed_when_expr == "enabled_in_stdout":
        changed = "Enabled" in simulated_stdout
    else:
        changed = True

    return {"skipped": False, "changed": changed, "rc": simulated_rc, "stdout": simulated_stdout}


def compute_serial_batches(hosts: Sequence[str], serial_spec: Sequence[int | str]) -> List[List[str]]:
    """Model Section 6 `serial: [1, '10%', '100%']` progressive batch sizing."""
    total = len(hosts)
    rem = list(hosts)
    batches: List[List[str]] = []
    spec_idx = 0

    while rem:
        raw = serial_spec[min(spec_idx, len(serial_spec) - 1)]
        if isinstance(raw, str) and raw.endswith("%"):
            pct = float(raw[:-1])
            size = max(1, math.ceil(total * (pct / 100.0)))
        else:
            size = max(1, int(raw))
        batches.append(rem[:size])
        rem = rem[size:]
        if spec_idx < len(serial_spec) - 1:
            spec_idx += 1
    return batches
