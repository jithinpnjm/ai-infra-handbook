"""Chapter 4.4 model: YAML 1.1 vs 1.2 type-coercion rules, anchor/alias/merge-key
(`<<`) resolution, multi-line block chomping (`|`, `>`, `|-`, `|+`), and
Jinja2-style custom filter (`get_interface_speed`) & switchport/Slurm template
rendering.

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapter 3 ("Playbooks: A Beginning"):
  * YAML start (`---`) and end (`...`) markers, comments (`#`), strings, multiline
    `|` vs `>` and `|+`, booleans (`true`/`false`/`yes`/`no`/`on`/`off`), lists
    (inline `[...]` vs block `- `), dictionaries (inline `{...}` vs indented
    `key: value`), and pure YAML task dictionaries vs `key=value` string arguments.
  * `webservers.yml` -> `webservers-tls.yml` with `templates/nginx.conf.j2` and
    `templates/index.html.j2` (`{{ inventory_hostname }}`, `{{ server_name }}`,
    `{{ tls_dir }}{{ cert_file }}`).
- Christian Adell, Scott Lowe, Matt Oswalt & Jason Edelman, Network
  Programmability and Automation, 2nd ed. (network-programmability-and-automation-
  2nd-edition, NPA):
  * Chapter 8 ("Data Formats and Models"): Structured vs screen-scraping CLI output,
    markup (HTML) vs data serialization (YAML, XML, JSON, Protobuf, FlatBuffers),
    decoding/deserializing vs serializing/encoding, XML/XSD/XPath, JSON/JSON Schema,
    and YANG (RFC 6020 / 7950 `container`, `list`, `leaf`, `leaf-list`, `typedef`).
  * Chapter 9 ("Templates"): Jinja2 `Environment(loader=FileSystemLoader('.'))`,
    switchport templates (`GigabitEthernet0/1..3` trunk vs access VLANs), chained
    filters (`| upper | reverse`), custom Python filter `get_interface_speed`,
    XSLT, and Go `text/template` (`{{range}}`, `FuncMap`, `IfParse`).
"""
from typing import Dict, List, Sequence, Tuple


def classify_yaml11_unquoted_scalar(token: str) -> Tuple[str, object]:
    """Model Section 1 YAML 1.1 scalar type-coercion pitfalls (e.g., PyYAML):
    - 'yes', 'no', 'on', 'off', 'y', 'n', 'true', 'false' (case-insensitive) -> bool
    - '~', 'null', '' -> None
    - '1.10' -> float 1.1 (trailing zero lost!)
    - '010' -> octal int 8 in YAML 1.1
    - '0x1f' -> hex int 31
    - '22:30' -> sexagesimal int 1350 (22*60 + 30) in YAML 1.1
    """
    low = token.lower()
    if low in {"~", "null", ""}:
        return ("null", None)
    if low in {"true", "yes", "on", "y"}:
        return ("bool", True)
    if low in {"false", "no", "off", "n"}:
        return ("bool", False)
    if token.startswith("0x") or token.startswith("0X"):
        return ("int_hex", int(token, 16))
    if len(token) > 1 and token.startswith("0") and token.isdigit():
        return ("int_octal_yaml11", int(token, 8))
    if ":" in token and all(p.isdigit() for p in token.split(":")):
        parts = [int(p) for p in token.split(":")]
        val = 0
        for p in parts:
            val = val * 60 + p
        return ("int_sexagesimal_yaml11", val)
    try:
        if "." in token or "e" in low:
            return ("float", float(token))
        return ("int", int(token))
    except ValueError:
        return ("str", token)


def apply_yaml_block_chomping(lines: Sequence[str], style: str) -> str:
    """Model YAML block scalar indicators `|`, `|-`, `|+`, `>`, `>-`."""
    folded = style.startswith(">")
    body = " ".join(lines) if folded else "\n".join(lines)
    if style.endswith("-"):
        return body
    if style.endswith("+"):
        return body + "\n\n"
    return body + "\n"


def get_interface_speed(interface_name: str) -> int:
    """NPA Ch. 9 Example 9-9 custom Jinja filter returning default Mbps speed."""
    low = interface_name.lower()
    if "gigabit" in low:
        return 1000
    if "fast" in low:
        return 100
    return 0


def render_switchport_template(interfaces: Sequence[Dict[str, object]], chain_reverse: bool = False) -> str:
    """Model NPA Ch. 9 Examples 9-6 to 9-10 switchport Jinja template with
    trunk/access conditionals, `upper` (+ optional `reverse`) filter chaining,
    and custom `get_interface_speed` filter.
    """
    out_lines: List[str] = []
    for iface in interfaces:
        name = str(iface["name"])
        desc = str(iface["desc"]).upper()
        if chain_reverse:
            desc = desc[::-1]
        out_lines.append(f"interface {name}")
        out_lines.append(f"  description {desc}")
        if iface.get("uplink"):
            out_lines.append("  switchport mode trunk")
        else:
            out_lines.append(f"  switchport access vlan {iface['vlan']}")
            out_lines.append("  switchport mode access")
        out_lines.append(f"  speed {get_interface_speed(name)}")
    return "\n".join(out_lines)


def render_slurm_nodes_template(nodes: Sequence[Dict[str, object]]) -> str:
    """Model Section 3 Slurm node definition template with StrictUndefined check."""
    lines: List[str] = []
    for n in sorted(nodes, key=lambda d: str(d["name"])):
        for req in ("name", "addr", "cpus", "mem_mb"):
            if req not in n or n[req] is None:
                raise KeyError(f"StrictUndefined: {req!r} is undefined")
        real_mem = int(int(n["mem_mb"]) * 0.95)  # type: ignore[arg-type]
        gpus = n.get("gpus", 8)
        lines.append(
            f"NodeName={n['name']} NodeAddr={n['addr']} CPUs={n['cpus']} RealMemory={real_mem} Gres=gpu:{gpus} State=UNKNOWN"
        )
    names = ",".join(str(n["name"]) for n in sorted(nodes, key=lambda d: str(d["name"])))
    lines.append(f"PartitionName=gpu Nodes={names} Default=YES MaxTime=INFINITE State=UP")
    return "\n".join(lines)
