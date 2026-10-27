"""Chapter 4.14 model: Wall-clock runtime estimator for `linear` vs `free`
strategies with straggler hosts, SSH multiplexing (`ControlPersist` `0.319s ->
0.010s`) & `pipelining` round-trip savings (`AUR` Ch. 20), and `jsonl_audit`
callback record formatter masking `no_log: true` tasks (`AUR` Ch. 18).

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapters 18 & 20:
  * Chapter 18 ("Callback Plug-ins"): Stdout plugins (only one active at a time:
    `default`, `yaml`, `debug`, `dense`, `minimal`, `json`, ` actionable`, `selective`,
    `oneline`, `unixy`) vs Notification/other plugins (multiple active via
    `callbacks_enabled` / `callback_whitelist`: `timer`, `profile_tasks`,
    `profile_roles`, `junit`, `slack`, `mail`, `foreman`, `logstash`, `logentries`,
    `say`, and **ARA** `ara[server]` / `ara-manage runserver`).
  * Chapter 20 ("Making Ansible Go Faster"): SSH multiplexing (`ControlMaster auto`,
    `ControlPersist 30m`, `ssh -O check` / `ssh -O exit`, dropping connection
    time from `0.319s` to `0.010s`), EC2 long-hostname Unix domain socket 104/108-byte
    limit (`control_path = %(directory)s/%%C`), `pipelining = True` and disabling
    `requiretty` in `/etc/sudoers.d/disable-requiretty` validated with
    `bash -c "cat /etc/sudoers /etc/sudoers.d/* %s | visudo -cf-"`, Mitogen,
    Fact Caching (`jsonfile`, `yaml`, `pickle`, `redis`, `memcached`, `86400`s),
    `forks`, `async` + `poll: 0` overlapping git clone with apt installs, and
    fast Ed25519 / `chacha20-poly1305@openssh.com` SSH cipher selection.
"""
import json
import math
from typing import Any, Dict, List, Sequence


def estimate_play_wall_clock_seconds(
    num_hosts: int,
    forks: int,
    task_durations_normal: Sequence[float],
    straggler_duration_multiplier: float = 1.0,
    strategy: str = "linear",
    ssh_handshake_s: float = 0.319,
    multiplexed_handshake_s: float = 0.010,
    use_control_persist: bool = True,
    use_pipelining: bool = True,
) -> float:
    """Estimate wall-clock execution time for a play across `num_hosts` with
    `forks` workers under `linear` vs `free` strategy, modeling:
    - SSH round trips per task: 3 without pipelining (mkdir/copy/exec) vs 1 with pipelining.
    - SSH connection cost: `ssh_handshake_s` (0.319s) without ControlPersist vs
      `multiplexed_handshake_s` (0.010s) after the first connection.
    - Straggler effect: under `linear`, every task wave waits for the slowest host
      in the batch (`d * straggler_duration_multiplier`).
    """
    waves = math.ceil(num_hosts / max(1, forks))
    ssh_trips_per_task = 1 if use_pipelining else 3

    def _conn_cost(task_idx: int, trip_idx: int) -> float:
        if not use_control_persist:
            return ssh_handshake_s
        return ssh_handshake_s if (task_idx == 0 and trip_idx == 0) else multiplexed_handshake_s

    if strategy == "linear":
        total = 0.0
        for t_idx, base_d in enumerate(task_durations_normal):
            trips_cost = sum(_conn_cost(t_idx, tr) for tr in range(ssh_trips_per_task))
            slowest_task_d = base_d * straggler_duration_multiplier + trips_cost
            total += waves * slowest_task_d
        return round(total, 3)

    if strategy == "free":
        # Under free, normal hosts do not wait for the single straggler on every task
        per_normal_host = sum(
            base_d + sum(_conn_cost(t_idx, tr) for tr in range(ssh_trips_per_task))
            for t_idx, base_d in enumerate(task_durations_normal)
        )
        straggler_host = sum(
            base_d * straggler_duration_multiplier + sum(_conn_cost(t_idx, tr) for tr in range(ssh_trips_per_task))
            for t_idx, base_d in enumerate(task_durations_normal)
        )
        return round(max((waves - 1) * per_normal_host + straggler_host, waves * per_normal_host), 3)

    raise ValueError(f"unsupported strategy {strategy!r}")


def format_jsonl_audit_event(
    *,
    event: str,
    host: str,
    task: str,
    changed: bool,
    rc: int,
    msg: str,
    no_log: bool = False,
) -> str:
    """Model Section 5 `jsonl_audit.py` callback plugin masking `msg` when `no_log=True`."""
    rec: Dict[str, Any] = {
        "event": event,
        "host": host,
        "task": task,
        "changed": changed,
        "rc": rc,
        "msg": msg[:500],
    }
    if no_log:
        rec.pop("msg", None)
    return json.dumps(rec, sort_keys=True)
