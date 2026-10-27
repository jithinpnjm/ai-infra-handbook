"""Chapter 4.3 model: `ansible.cfg` discovery precedence, INI inventory host-pattern
matching (`all`, union `:`, intersection `:&`, exclusion `:!`, wildcard `*`,
regex `~`), and idempotent module state evaluation (`ok` vs `changed`).

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapters 1 & 2:
  * Chapter 1 ("Introduction"): Origin of the name "Ansible" (Ursula K. Le Guin's
    1966 Rocannon's World & Orson Scott Card's 1985 Ender's Game via Michael
    DeHaan), 3-tier content reorganization (Core, Certified, Community),
    4-step parallel lockstep task execution on `web1..web3`, system abstraction
    (`file` module replacing `mkdir -p` + `chown` + `chmod`), top-to-bottom single-run
    execution vs CFEngine convergence, push-based vs Puppet/Chef pull agents,
    `ansible-pull`, and `ansible_runner.run()` Python embedding.
  * Chapter 2 ("Installation and Setup"): Control-machine venv (`python3 -m venv .venv --prompt A`),
    Vagrant test server (`vagrant init ubuntu/focal64`, `vagrant up`, `vagrant ssh-config`
    port `2222` & `.vagrant/machines/default/virtualbox/private_key`, forwarded ports
    `8080->80`/`8443->443`, private network `192.168.33.10`, `forward_agent`,
    `ansible_local` vs `ansible` provisioners, `config.json` multi-VM Ruby loop),
    4-level `ansible.cfg` search order (`ANSIBLE_CONFIG`, `./ansible.cfg`,
    `~/.ansible.cfg`, `/etc/ansible/ansible.cfg`), ad-hoc `ping`/`command`
    (`-a uptime`, `-b -a "tail /var/log/syslog"`), and why restrictive command-specific
    `sudoers` or `rbash` fail on Ansible's random `~/.ansible/tmp` script paths.
"""
import fnmatch
import re
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple


def resolve_ansible_cfg_path(
    env_ansible_config: Optional[str],
    cwd_cfg_exists: bool,
    cwd_world_writable: bool,
    home_cfg_exists: bool,
    etc_cfg_exists: bool = True,
) -> str:
    """Model AUR Ch. 2 & Section 4 `ansible.cfg` 4-step search order (first found
    wins, not merged; `./ansible.cfg` is ignored if world-writable for security).
    """
    if env_ansible_config:
        return env_ansible_config
    if cwd_cfg_exists and not cwd_world_writable:
        return "./ansible.cfg"
    if home_cfg_exists:
        return "~/.ansible.cfg"
    if etc_cfg_exists:
        return "/etc/ansible/ansible.cfg"
    return "defaults_only"


def match_host_pattern(groups: Mapping[str, Sequence[str]], pattern: str) -> List[str]:
    """Evaluate Ansible host patterns (`all`, group, union `:`, intersection `:&`,
    exclusion `:!`, glob `*`, and regex `~`) preserving deterministic order.
    """
    all_hosts: List[str] = []
    for members in groups.values():
        for h in members:
            if h not in all_hosts:
                all_hosts.append(h)

    def _expand_token(tok: str) -> Set[str]:
        if tok == "all" or tok == "*":
            return set(all_hosts)
        if tok.startswith("~"):
            rx = re.compile(tok[1:])
            return {h for h in all_hosts if rx.search(h)}
        if tok in groups:
            return set(groups[tok])
        if "*" in tok or "?" in tok or "[" in tok:
            return {h for h in all_hosts if fnmatch.fnmatch(h, tok)}
        return {tok} if tok in all_hosts else set()

    parts = pattern.split(":")
    selected: Set[str] = set()
    for idx, part in enumerate(parts):
        if idx == 0:
            selected = _expand_token(part)
        elif part.startswith("&"):
            selected &= _expand_token(part[1:])
        elif part.startswith("!"):
            selected -= _expand_token(part[1:])
        else:
            selected |= _expand_token(part)

    return [h for h in all_hosts if h in selected]


def simulate_idempotent_file_module(
    fs_state: Dict[str, Dict[str, str]],
    path: str,
    owner: str,
    group: str,
    mode: str,
    state: str = "directory",
    check_mode: bool = False,
) -> Dict[str, object]:
    """Model AUR Ch. 1 `file` module (`path=/etc/skel/.ssh mode=0700 owner=root
    group=root state=directory`): return `changed=True` on first run (or in
    `--check` mode without mutating `fs_state`) and `changed=False` when already
    in the desired state.
    """
    desired = {"owner": owner, "group": group, "mode": mode, "state": state}
    current = fs_state.get(path)
    if current == desired:
        return {"changed": False, "status": "ok", "state": dict(current)}
    if not check_mode:
        fs_state[path] = dict(desired)
    return {"changed": True, "status": "changed", "state": dict(desired)}
