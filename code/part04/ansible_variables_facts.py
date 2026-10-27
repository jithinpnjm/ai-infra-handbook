"""Chapter 4.7 model: Ansible variables, registered results (`stat.isdir`, `rc`,
`stdout_lines`), local custom facts (`/etc/ansible/facts.d/*.fact` ->
`ansible_local`), magic variables (`hostvars`, `groups` cross-host HAProxy /
`/etc/hosts` / Prometheus target projection via `extract`), and `dict2items` /
`items2dict` / `combine` filters.

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapter 5 ("Variables and Facts"):
  * Defining variables in playbooks (`vars:`, `vars_files: [nginx.yml]`),
    string concatenation with `~` (`"https://" ~ server_name ~ "/index.html"`),
    and variable naming restrictions (letters, numbers, underscores; no hyphens/spaces/dots).
  * `register` capturing command (`whoami`) and `stat` module outputs
    (`result.stat.mode` vs `result['stat']['mode']` and why bracket notation
    beats dot notation when keys collide with Python dict methods like `.values`),
    and branching on `result.stat.exists and result.stat.isdir`.
  * Facts (`setup` module with `filter=ansible_eth*` / `ansible_all_ipv6_addresses`),
    local custom facts in `/etc/ansible/facts.d/example.fact` (`[book] title=...` ->
    `ansible_local.example.book.title`), `set_fact`, built-in magic variables
    (`hostvars`, `inventory_hostname`, `groups` iterating `groups.web` to render
    HAProxy `backend web-backend` server lines), and `-e @greetvars.yml` precedence.
"""
import configparser
import io
import json
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def parse_local_fact_file(filename: str, content: str) -> Dict[str, Any]:
    """Model Section 3 & AUR Ch. 5 Example 5-10 `/etc/ansible/facts.d/<name>.fact`
    (INI or JSON) loaded under `ansible_local.<name>`.
    """
    stem = filename.rsplit("/", 1)[-1]
    if stem.endswith(".fact"):
        stem = stem[:-5]
    stripped = content.lstrip()
    if stripped.startswith("{"):
        return {stem: json.loads(content)}
    cp = configparser.ConfigParser()
    cp.read_file(io.StringIO(content))
    parsed: Dict[str, Dict[str, str]] = {sec: dict(cp.items(sec)) for sec in cp.sections()}
    return {stem: parsed}


def project_group_hostvars(
    groups: Mapping[str, Sequence[str]],
    hostvars: Mapping[str, Mapping[str, Any]],
    group_name: str,
    attr: str,
) -> List[Any]:
    """Model `groups[group_name] | map('extract', hostvars, attr) | list`
    and verify that facts must be gathered for all referenced hosts.
    """
    out: List[Any] = []
    for host in groups.get(group_name, ()):
        hv = hostvars.get(host, {})
        if attr not in hv:
            raise KeyError(f"hostvars[{host!r}][{attr!r}] is undefined (did you gather facts on {host}?)")
        out.append(hv[attr])
    return out


def render_haproxy_backend_from_groups(
    groups: Mapping[str, Sequence[str]],
    hostvars: Mapping[str, Mapping[str, Any]],
    group_name: str = "web",
    port: int = 80,
) -> str:
    """Model AUR Ch. 5 HAProxy `backend web-backend` template iterating `groups.web`
    and reading `hostvars[host].ansible_default_ipv4.address`.
    """
    lines = ["backend web-backend"]
    for host in groups.get(group_name, ()):
        ip = hostvars[host]["ansible_default_ipv4"]["address"]
        lines.append(f"  server {host} {ip}:{port}")
    return "\n".join(lines)


def dict2items_and_items2dict_roundtrip(d: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Model Ansible's `dict2items` and `items2dict` filters."""
    items = [{"key": k, "value": v} for k, v in d.items()]
    reconstructed = {entry["key"]: entry["value"] for entry in items}
    return items, reconstructed
