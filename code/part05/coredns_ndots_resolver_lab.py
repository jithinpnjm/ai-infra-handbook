#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.11: DNS and service discovery with CoreDNS."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from coredns_ndots_resolver import (
    detect_coredns_forwarding_loop,
    expand_dns_search_queries,
    resolve_headless_service_records,
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
    # 1. Section 2 & NK Ch. 5: ndots:5 vs ndots:2 vs trailing dot on external name 'api.huggingface.co'
    q_ndots5 = expand_dns_search_queries("api.huggingface.co", namespace="ml", ndots=5)
    q_ndots2 = expand_dns_search_queries("api.huggingface.co", namespace="ml", ndots=2)
    q_fqdn = expand_dns_search_queries("api.huggingface.co.", namespace="ml", ndots=5)
    q_incluster_ndots2 = expand_dns_search_queries("vllm.serving", namespace="ml", ndots=2)
    check(
        "ndots=5 expands 'api.huggingface.co' (2 dots) into 8 queries (6 NXDOMAIN + 2 answer), whereas ndots=2 or trailing dot takes 2 queries while preserving 1-dot 'vllm.serving' search",
        len(q_ndots5) == 8
        and q_ndots5[0] == "A api.huggingface.co.ml.svc.cluster.local."
        and len(q_ndots2) == 2
        and len(q_fqdn) == 2
        and q_incluster_ndots2[0] == "A vllm.serving.ml.svc.cluster.local.",
    )

    # 2. Section 1 & 5: Headless Service + StatefulSet peer discovery with publishNotReadyAddresses
    pods = [
        {"name": "trainer-0", "ip": "10.244.1.10", "ready": True},
        {"name": "trainer-1", "ip": "10.244.2.11", "ready": False},  # waiting for peer rendezvous!
    ]
    rec_default = resolve_headless_service_records("trainer", "ml", pods, publish_not_ready_addresses=False)
    rec_pub_not_ready = resolve_headless_service_records("trainer", "ml", pods, publish_not_ready_addresses=True)
    check(
        "Headless Service omits unready trainer-1 by default and publishes trainer-1.trainer.ml.svc.cluster.local when publishNotReadyAddresses=True",
        "trainer-1.trainer.ml.svc.cluster.local." not in rec_default
        and rec_pub_not_ready["trainer-1.trainer.ml.svc.cluster.local."] == ["10.244.2.11"]
        and len(rec_pub_not_ready["trainer.ml.svc.cluster.local."]) == 2,
    )

    # 3. Section 3 & 7: CoreDNS loop plugin detection on 127.0.0.53
    has_loop, _ = detect_coredns_forwarding_loop(["127.0.0.53"])
    no_loop, _ = detect_coredns_forwarding_loop(["10.0.0.2", "8.8.8.8"])
    check(
        "detect_coredns_forwarding_loop flags 127.0.0.53 systemd-resolved loop and accepts real upstream resolvers",
        has_loop is True and no_loop is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
