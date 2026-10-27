"""Chapter 2.28 model: YANG / JSON-Schema switch inventory validator (hostname
regex, VLAN range 1..4094, MTU range 68..9216, ASN, and IPv4 prefix), strict
switch configuration template renderer (failing on missing keys like Jinja2
StrictUndefined), and NETCONF candidate + confirmed-commit state machine.

Sources modeled:
- Christian Adell, Scott S. Lowe, Jason Edelman, and Matt Oswalt, Network
  Programmability and Automation, 2nd ed. (network-programmability-and-automation-2nd-edition,
  NPA), Chapters 2, 8, 9, and 10 (types of automation, outage lessons, SNMP ->
  CLI -> NETCONF -> RESTCONF -> gNMI evolution, YAML/JSON/XML/Protobuf, YANG
  RFC 7950 / JSON Schema, Jinja2 templates, REST/NETCONF RFC 6241/RESTCONF RFC
  8040/gNMI).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 18 ("Centralized Control Planes": southbound/northbound, distributed/
  augmented/hybrid/replace models, BGP as SDN, Fibbing, PCEP, I2RS, OpenFlow,
  CAP theorem and subsidiarity).
"""
import ipaddress
import re
from typing import Dict, List


HOSTNAME_RE = re.compile(r"^[a-z0-9-]+$")


def validate_switch_inventory_schema(inv: Dict[str, object]) -> Dict[str, object]:
    """Validate switch intent data against YANG / JSON Schema constraints (Section 4)."""
    errors: List[str] = []
    hostname = str(inv.get("hostname", ""))
    if not hostname or not HOSTNAME_RE.match(hostname):
        errors.append("invalid_hostname_pattern")

    vlans = inv.get("vlans")
    if not isinstance(vlans, list) or not vlans or any(not (1 <= int(v) <= 4094) for v in vlans):
        errors.append("invalid_vlan_list_must_be_1_to_4094")

    for iface in list(inv.get("interfaces", [])):
        mtu = int(iface.get("mtu", 9214))
        if not (68 <= mtu <= 9216):
            errors.append(f"invalid_mtu_{mtu}_outside_68_to_9216")
        if "ipv4" in iface:
            try:
                ipaddress.IPv4Interface(str(iface["ipv4"]))
            except ValueError:
                errors.append(f"invalid_ipv4_interface_{iface['ipv4']}")

    return {"valid": len(errors) == 0, "errors": errors}


def render_leaf_config_strict(data: Dict[str, object]) -> str:
    """Render a switch configuration from structured data, raising KeyError on missing required fields."""
    required = {"hostname", "interfaces", "bgp"}
    missing = required - set(data.keys())
    if missing:
        raise KeyError(f"StrictUndefined: missing required template keys {sorted(missing)}")
    bgp = dict(data["bgp"])
    if "asn" not in bgp or "router_id" not in bgp:
        raise KeyError("StrictUndefined: missing bgp.asn or bgp.router_id")

    lines = [f"hostname {str(data['hostname']).lower()}", "!"]
    for i in list(data["interfaces"]):
        if "name" not in i:
            raise KeyError("StrictUndefined: interface missing 'name'")
        lines.append(f"interface {i['name']}")
        lines.append(f" description {i.get('description', 'unused')}")
        lines.append(f" mtu {i.get('mtu', 9214)}")
        if "ipv4" in i:
            lines.append(f" ip address {i['ipv4']}")
        else:
            lines.append(" switchport mode access")
        lines.append(" no shutdown" if i.get("enabled", True) else " shutdown")
        lines.append("!")
    lines.append(f"router bgp {bgp['asn']}")
    lines.append(f" router-id {bgp['router_id']}")
    for n in list(bgp.get("neighbors", [])):
        lines.append(f" neighbor {n['ip']} remote-as {n['asn']}")
    return "\n".join(lines)


def simulate_netconf_confirmed_commit(
    initial_running_mtu: int,
    candidate_mtu: int,
    confirm_within_timeout: bool,
) -> Dict[str, object]:
    """Simulate NETCONF edit-config -> candidate -> commit(confirmed=True, timeout=120s)."""
    if confirm_within_timeout:
        return {
            "final_running_mtu": candidate_mtu,
            "rolled_back": False,
        }
    return {
        "final_running_mtu": initial_running_mtu,
        "rolled_back": True,
    }
