"""Chapter 4.8 model: Ansible handlers (`notify`, `listen` topics, lost-handler-on-
failure vs `force_handlers: true`), custom `FilterModule` (`surround_by_quotes`
from `AUR` Ch. 10), `block` / `rescue` / `always` state machine (with VM snapshot
rollback vs leaving GPU node DRAINED), and `import_tasks` (static) vs
`include_tasks` (dynamic) behavior.

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapters 10 & 11:
  * Chapter 10 ("Making Playbooks Appear More Complex"): `changed_when` on
    `django_manage createdb` (`"Creating tables" in result.out`), custom filter
    plugin `FilterModule.surround_by_quotes` in `filter_plugins/surround_by_quotes.py`,
    filepath filters (`basename`, `dirname`, `expanduser`, `realpath`), lookups
    (`file`, `pipe`, `env`, `password`, `csvfile`, `dig`, `redis`), looping
    constructs (`loop`, `with_items`, `with_lines`, `with_fileglob`, `with_dict`,
    `with_subelements`, `loop_control: { loop_var: vhost }`), and `block`/`rescue`/`always`
    in `app-upgrade.yml` (`cs_loadbalancer_rule_member`, `cs_vmsnapshot` revert on
    rescue).
  * Chapter 11 ("Execution Strategies and Flow Control"): `linear` vs `free` vs
    `debug` strategies, `delegate_to: localhost` (Nagios alerts, EC2 ELB drain,
    `run_once: true` downloading `goss` binary via proxy once onto control node),
    and handler chaining / `listen: Ssl_certs_changed` topic fan-out (`check nginx
    configuration` -> `restart nginx` -> `after config check`).
"""
from typing import Dict, List, Sequence, Tuple


class FilterModule:
    """AUR Ch. 10 Example 10-11 filter_plugins/surround_by_quotes.py."""

    @staticmethod
    def surround_by_quotes(a_list: Sequence[str]) -> List[str]:
        return [f'"{x}"' for x in a_list]

    def filters(self):
        return {"surround_by_quotes": self.surround_by_quotes}


def simulate_handler_listen_and_failure_loss(
    *,
    config_changed_run1: bool,
    later_task_failed_run1: bool,
    force_handlers: bool = False,
) -> Dict[str, List[str]]:
    """Model Section 1 & AUR Ch. 11 handler `listen` topic fan-out and the
    "lost handler after failure" trap across two consecutive runs:
    - Run 1: config task changes and notifies topic `'Ssl_certs_changed'`
      (subscribed by `['check_nginx_config', 'restart_nginx', 'after_config_check']`).
      If a later task fails before flush and `force_handlers=False`, handlers do NOT run.
    - Run 2 (rerun after fixing the later task): because the config file was
      already written during Run 1, the config task reports `changed=False` (`ok`),
      so handlers STILL do not run on Run 2 unless `force_handlers=True` (or
      `meta: flush_handlers`) was used!
    """
    topic_subscribers = ["check_nginx_config", "restart_nginx", "after_config_check"]
    run1_handlers: List[str] = []
    run2_handlers: List[str] = []

    if config_changed_run1 and (not later_task_failed_run1 or force_handlers):
        run1_handlers.extend(topic_subscribers)

    # On Run 2, the config file is already on disk from Run 1, so config_changed_run2 is False
    config_changed_run2 = not config_changed_run1
    if config_changed_run2:
        run2_handlers.extend(topic_subscribers)

    return {
        "run1_handlers": run1_handlers,
        "run2_handlers": run2_handlers,
    }


def simulate_block_rescue_always_maintenance(
    *,
    upgrade_succeeds: bool,
    validate_succeeds: bool,
    reraise_in_rescue: bool = True,
) -> Dict[str, object]:
    """Model Section 4 & 6 `block` / `rescue` / `always` GPU maintenance flow:
    1. Drain node (`state = 'DRAINED'`)
    2. `block`: run `apply_changes` and `validate`
    3. `rescue`: rollback driver; if `reraise_in_rescue`, fail host (leaving node `DRAINED`)
    4. `always`: collect kernel diagnostics (`journalctl -k`)
    5. Only if block succeeded without rescue failure, resume node (`state = 'RESUMED'`).
    """
    events: List[str] = ["drain_node"]
    node_state = "DRAINED"
    host_failed = False
    rescued = False

    try:
        events.append("block:apply_changes")
        if not upgrade_succeeds:
            raise RuntimeError("apply_changes failed")
        events.append("block:validate")
        if not validate_succeeds:
            raise RuntimeError("validate failed")
    except RuntimeError as exc:
        rescued = True
        events.append(f"rescue:rollback({exc})")
        if reraise_in_rescue:
            host_failed = True
            events.append("rescue:fail_loudly")
    finally:
        events.append("always:collect_diagnostics")

    if not host_failed and not rescued:
        node_state = "RESUMED"
        events.append("resume_node")

    return {
        "events": events,
        "node_state": node_state,
        "host_failed": host_failed,
        "rescued": rescued,
    }
