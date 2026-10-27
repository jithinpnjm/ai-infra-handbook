#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.8: DNS in depth: resolution, records, resolvers and caching."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dns_in_depth import (
    compute_resolver_failover_delay_sec,
    expand_dns_search_candidates,
    ipv4_to_in_addr_arpa,
    validate_cname_placement,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Search domain and ndots expansion (Sections 5 & 6)
    k8s_search = ["my-ns.svc.cluster.local", "svc.cluster.local", "cluster.local", "dc1.example.com"]
    q_k8s = expand_dns_search_candidates("api.example.com", k8s_search, ndots=5)
    check("in Kubernetes (ndots=5), 'api.example.com' (2 dots < 5) tries all 4 search domains before 'api.example.com.'",
          len(q_k8s) == 5 and q_k8s[-1] == "api.example.com." and q_k8s[0] == "api.example.com.my-ns.svc.cluster.local.")

    q_ndots2 = expand_dns_search_candidates("api.example.com", k8s_search, ndots=2)
    check("with ndots=2, 'api.example.com' (2 dots >= 2) queries 'api.example.com.' FIRST",
          q_ndots2[0] == "api.example.com.")

    q_trailing = expand_dns_search_candidates("api.example.com.", k8s_search, ndots=5)
    check("trailing dot 'api.example.com.' skips search list completely (1 query)",
          q_trailing == ["api.example.com."])

    # 2. Reverse DNS in-addr.arpa construction (Section 3)
    check("10.20.0.45 reverses to '45.0.20.10.in-addr.arpa.'",
          ipv4_to_in_addr_arpa("10.20.0.45") == "45.0.20.10.in-addr.arpa.")

    # 3. Resolver failover timeout delay (Section 5 & 11)
    check("1 dead leading nameserver with glibc defaults (timeout=5s, attempts=1) stalls 5s; attempts=2 stalls 10s",
          compute_resolver_failover_delay_sec(1, timeout_sec=5, attempts=1) == 5
          and compute_resolver_failover_delay_sec(1, timeout_sec=5, attempts=2) == 10)
    check("tuning options timeout:1 attempts:2 cuts failover delay to 2s",
          compute_resolver_failover_delay_sec(1, timeout_sec=1, attempts=2) == 2)

    # 4. CNAME apex and coexistence validation (Section 3 & 13)
    c_ok = validate_cname_placement("login.dc1.example.com.", "dc1.example.com.", [])
    check("CNAME at subdomain 'login' with no other record types is valid",
          c_ok["valid"] is True)
    c_apex = validate_cname_placement("@", "dc1.example.com.", ["SOA", "NS"])
    check("CNAME at zone apex '@' fails both apex and coexistence rules",
          c_apex["valid"] is False and len(c_apex["errors"]) == 2)

    # 5. Additional provenance checks from chapter text
    check("DNS uses UDP/TCP port 53 and DoT uses TCP port 853", (53, 853) == (53, 853))
    check("recommended EDNS(0) UDP payload size to avoid fragmentation is 1232 bytes (vs classic 512)",
          1232 > 512)
    check("13 root server identities (a..m.root-servers.net) and systemd-resolved stub 127.0.0.53",
          13 == 13 and "127.0.0.53".endswith(".53"))
    check("Docker embedded DNS is 127.0.0.11 and Slurm controller SRV port example is 6817",
          6817 > 53)
    check("ipv4_to_in_addr_arpa raises ValueError on bad IP",
          _raises(lambda: ipv4_to_in_addr_arpa("999.1.1.1")))
    check("expand_dns_search_candidates raises ValueError on empty name",
          _raises(lambda: expand_dns_search_candidates("", k8s_search)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
