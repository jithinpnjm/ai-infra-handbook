"""Chapter 4.10 model: Ansible failure-layer classifier (Parse vs Connection
`UNREACHABLE` vs Data/Template vs Privilege/Module vs Application), interactive
Task Debugger state simulator (`p task`, `p task.args`, `p task_vars`,
`update_task`, `redo`), and `stat` module return-value assertions (`AUR` Ch. 8
Table 8-3).

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapter 8 ("Debugging Ansible
  Playbooks"):
  * Human-friendly output (`stdout_callback = yaml` / `debug`), `-v` to `-vvvv`
    SSH debug output (`SSH: EXEC ssh -vvv -4 -o PreferredAuthentications=publickey
    -o ForwardAgent=yes`), and `log_path`.
  * Common SSH challenges: `PasswordAuthentication no`, `Host Key Verification
    Failed` (`ssh-keygen -R 192.168.33.10` + `ssh-keyscan 192.168.33.10 >> ~/.ssh/known_hosts`),
    bastion jump hosts (`ProxyJump`), `nc hostname 2222` banner check, and
    `authorized_key` `key_options: 'no-port-forwarding,from="93.184.216.34"'` +
    `exclusive: true`.
  * The Ansible Task Debugger (`debugger: always|on_failed|on_unreachable|on_skipped`,
    `p task`, `p task.args`, `p result`, `p vars`, `p vars[key]`, `task.args[key] = val`,
    `vars[key] = val` + `u`/`update_task`, `r`/`redo`, `c`/`continue`, `q`/`quit`).
  * Testing Before Execution (`--syntax-check`, `--list-tasks`, `--list-hosts`,
    `--check -D`/`--diff`, `--step`, `--start-at-task`, `tags`) and `assert` with
    `stat` module return values (`exists`, `isdir`, `isreg`, `islnk`, `pw_name`,
    `uid`, `gid`, `mode`, `checksum`, `md5`).
"""
from typing import Any, Dict, List


def classify_ansible_failure_layer(error_text: str) -> str:
    """Classify an Ansible error message into one of the 5 diagnostic layers
    from Section 1 & 5:
      - 'parse_or_syntax'
      - 'connection_unreachable'
      - 'data_or_template'
      - 'privilege_or_module'
      - 'application_command'
    """
    if any(
        pat in error_text
        for pat in (
            "Syntax Error while loading YAML",
            "mapping values are not allowed here",
            "found unacceptable key",
            "is not a valid attribute for a Task",
            "couldn't resolve module/action",
        )
    ):
        return "parse_or_syntax"

    if any(
        pat in error_text
        for pat in (
            "UNREACHABLE",
            "Permission denied (publickey",
            "Host key verification failed",
            "Connection timed out",
            "Could not resolve hostname",
            "kex_exchange_identification",
        )
    ):
        return "connection_unreachable"

    if any(
        pat in error_text
        for pat in (
            "undefined variable",
            "AnsibleUndefinedVariable",
            "template error while templating string",
            "Conditional result was derived from a non-boolean",
            "conditional check failed",
        )
    ):
        return "data_or_template"

    if any(
        pat in error_text
        for pat in (
            "Missing sudo password",
            "a terminal is required",
            "/usr/bin/python: not found",
            "Failed to set permissions on the temporary files",
            "MODULE FAILURE",
            "Unsupported parameters for",
        )
    ):
        return "privilege_or_module"

    return "application_command"


class InteractiveTaskDebuggerSession:
    """Model AUR Ch. 8 Table 8-2 & Section 4 interactive task debugger commands."""

    def __init__(self, task_name: str, args_template: Dict[str, str], task_vars: Dict[str, Any]) -> None:
        self.task_name = task_name
        self._raw_args = dict(args_template)
        self.task_vars = dict(task_vars)
        self.args = self._render_args()
        self.status = "failed"

    def _render_args(self) -> Dict[str, str]:
        rendered: Dict[str, str] = {}
        for k, v in self._raw_args.items():
            if v.startswith("{{") and v.endswith("}}"):
                var_name = v[2:-2].strip()
                rendered[k] = str(self.task_vars.get(var_name, "UNDEFINED"))
            else:
                rendered[k] = v
        return rendered

    def set_var_and_update_task(self, key: str, value: Any) -> Dict[str, str]:
        """Simulate `task_vars[key] = value` followed by `u` / `update_task`."""
        self.task_vars[key] = value
        self.args = self._render_args()
        return dict(self.args)

    def redo(self, valid_packages: set[str]) -> str:
        """Simulate `r` / `redo` re-executing the task with updated args."""
        if self.args.get("name") in valid_packages:
            self.status = "ok"
        else:
            self.status = "failed"
        return self.status
