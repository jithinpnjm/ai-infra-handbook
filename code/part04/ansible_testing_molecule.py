"""Chapter 4.13 model: Molecule scenario lifecycle runner (`create`, `prepare`,
`converge`, `idempotence`, `side_effect`, `verify`, `destroy`), Goss YAML
verifier (`test_sshd.yml` from `AUR` Ch. 14 Example 14-7), and `ansible-lint`
rule checker.

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapters 14 & 22:
  * Chapter 14 ("Quality Assurance with Molecule"): `yamllint`, `ansible-lint`,
    `ansible-later` (`.later.yml`), Molecule history (created in 2015 by
    `@retr0h`), Molecule drivers (`delegated`, `docker`, `podman`, `vagrant`,
    `azure`, `ec2`, `gce`, `hetznercloud`, `linode`), multi-container custom
    Docker network (`redis` `10.16.0.0/24` with `redis1_centos7` `10.16.0.10`,
    `10.16.0.11`, `10.16.0.12` in `redis_server` and `redis_sentinel` groups),
    `desired_state` (`present.yml` vs `absent.yml`), Goss verifier (`test_sshd.yml`
    checking `/etc/ssh/ssh_host_ed25519_key.pub`, `tcp:22`, `sshd` service/user/group/process
    with TAP output `1..18`), and Testinfra (`testinfra.utils.ansible_runner`).
  * Chapter 22 ("CI/CD and Ansible"): Declarative `Jenkinsfile` mapping Molecule
    stages (`syntax`, `lint`, `converge`, `verify`, `idempotence`).
"""
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple


def check_ansible_lint_rules(task: Mapping[str, Any]) -> List[str]:
    """Model core `ansible-lint` production rules on a parsed task dict."""
    violations: List[str] = []
    if "name" not in task or not str(task["name"]).strip():
        violations.append("name[missing]")

    module_keys = [
        k
        for k in task.keys()
        if k not in {"name", "become", "when", "register", "changed_when", "failed_when", "tags", "loop", "args"}
    ]
    if len(module_keys) == 1:
        mod = module_keys[0]
        if "." not in mod:
            violations.append("fqcn[action-core]")
        short = mod.rsplit(".", 1)[-1]
        if short in {"command", "shell"}:
            cmd_str = str(task[mod])
            if any(cmd_str.startswith(bin_name) for bin_name in ("apt ", "apt-get ", "yum ", "dnf ", "systemctl ", "git ", "mkdir ")):
                violations.append("command-instead-of-module")
            args = task.get("args", {})
            if "changed_when" not in task and "creates" not in args and "removes" not in args:
                violations.append("no-changed-when")
            if short == "shell" and "|" in cmd_str and "pipefail" not in cmd_str:
                violations.append("risky-shell-pipe")
        if short in {"copy", "template", "file"} and isinstance(task[mod], Mapping):
            if "mode" not in task[mod] and task[mod].get("state") != "absent":
                violations.append("risky-file-permissions")
        if short in {"package", "apt", "dnf", "yum"} and isinstance(task[mod], Mapping):
            if task[mod].get("state") == "latest":
                violations.append("package-latest")

    return violations


def run_molecule_lifecycle(
    converge_fn: Callable[[Dict[str, Any]], int],
    side_effect_fn: Callable[[Dict[str, Any]], None],
    verify_fn: Callable[[Dict[str, Any]], bool],
) -> Dict[str, object]:
    """Model Section 4 Molecule `test` sequence:
      create -> converge (run 1) -> idempotence (run 2 must have changed == 0)
      -> side_effect (drift injection) -> converge (repair) -> verify -> destroy.
    """
    host_state: Dict[str, Any] = {"created": True}
    changed_run1 = converge_fn(host_state)
    changed_run2 = converge_fn(host_state)
    idempotent = changed_run2 == 0

    side_effect_fn(host_state)
    changed_after_drift = converge_fn(host_state)
    verified = verify_fn(host_state)
    host_state.clear()

    return {
        "changed_run1": changed_run1,
        "changed_run2": changed_run2,
        "idempotent": idempotent,
        "repaired_drift": changed_after_drift > 0,
        "verified": verified,
        "destroyed": len(host_state) == 0,
    }


def evaluate_goss_sshd_spec(host_state: Mapping[str, Any]) -> Tuple[int, int]:
    """Model AUR Ch. 14 Example 14-7 Goss `test_sshd.yml` TAP verifier (`1..6`)."""
    checks = [
        host_state.get("file_ed25519_pub_mode") == "0644",
        "ssh-ed25519 " in str(host_state.get("file_ed25519_pub_content", "")),
        host_state.get("port_tcp_22_listening") is True,
        host_state.get("service_sshd_enabled") is True,
        host_state.get("service_sshd_running") is True,
        host_state.get("user_sshd_exists") is True,
    ]
    return sum(1 for c in checks if c), len(checks)
