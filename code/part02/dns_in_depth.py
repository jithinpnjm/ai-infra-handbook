"""Chapter 2.8 model: resolv.conf search-domain and ndots expansion order,
IPv4 reverse-DNS in-addr.arpa label construction, glibc resolver failover
timeout calculation, and zone-file CNAME coexistence / apex validation.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9
  ("Resolving Hostnames": /etc/hosts, /etc/resolv.conf, /etc/nsswitch.conf,
  systemd-resolved, host tool) and Chapter 10 (network applications).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 5 (addressing, multiplexing, transport) and Chapter 6 (DNS interlayer
  discovery).
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapters 1,
  2, and 4 (CoreDNS, ndots:5 search expansion, headless services).
"""
from typing import Dict, List


def expand_dns_search_candidates(
    qname: str,
    search_domains: List[str],
    ndots: int = 1,
) -> List[str]:
    """Return the ordered list of FQDNs queried by a stub resolver for qname."""
    if ndots < 0:
        raise ValueError("ndots must be non-negative")
    clean = qname.strip()
    if not clean:
        raise ValueError("qname must be non-empty")
    # Trailing dot means explicit absolute FQDN: skip search list
    if clean.endswith("."):
        return [clean]
    dot_count = clean.count(".")
    with_search = [f"{clean}.{dom.strip('.')}." for dom in search_domains]
    absolute = f"{clean}."
    if dot_count >= ndots:
        return [absolute] + with_search
    return with_search + [absolute]


def ipv4_to_in_addr_arpa(ipv4_str: str) -> str:
    """Convert an IPv4 address ('10.20.0.45') into its reverse PTR name ('45.0.20.10.in-addr.arpa.')."""
    octets = ipv4_str.strip().split(".")
    if len(octets) != 4 or any(not (o.isdigit() and 0 <= int(o) <= 255) for o in octets):
        raise ValueError(f"Invalid IPv4 address: {ipv4_str}")
    return ".".join(reversed(octets)) + ".in-addr.arpa."


def compute_resolver_failover_delay_sec(
    num_dead_leading_servers: int,
    timeout_sec: int = 5,
    attempts: int = 2,
) -> int:
    """Compute worst-case delay in seconds before falling over past dead nameservers."""
    if num_dead_leading_servers < 0 or timeout_sec <= 0 or attempts <= 0:
        raise ValueError("Invalid resolver timeout parameters")
    return num_dead_leading_servers * timeout_sec * attempts


def validate_cname_placement(
    owner_name: str,
    zone_apex: str,
    coexisting_record_types: List[str],
) -> Dict[str, object]:
    """Validate RFC 1034/2181 CNAME rules: not allowed at zone apex and cannot coexist with A/MX/NS/SOA/TXT."""
    is_apex = owner_name.rstrip(".") == zone_apex.rstrip(".") or owner_name == "@"
    non_dnssec_others = [t for t in coexisting_record_types if t not in {"RRSIG", "NSEC", "NSEC3"}]
    errors: List[str] = []
    if is_apex:
        errors.append("cname_not_allowed_at_zone_apex")
    if non_dnssec_others:
        errors.append("cname_cannot_coexist_with_other_record_types")
    return {"valid": len(errors) == 0, "errors": errors}
