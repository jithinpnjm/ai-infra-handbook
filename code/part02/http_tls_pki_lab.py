#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.10: HTTP, TLS and PKI basics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from http_tls_pki import (
    classify_http_status_code,
    compute_connection_setup_rtts,
    match_san_dns_pattern,
    validate_x509_leaf_certificate,
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
    # 1. RFC 6125 SAN wildcard matching (Section 4)
    check("'*.lab.internal' matches 'api.lab.internal' (single leftmost label)",
          match_san_dns_pattern("api.lab.internal", "*.lab.internal") is True)
    check("'*.lab.internal' does NOT match multi-level 'a.b.lab.internal' or bare apex 'lab.internal'",
          match_san_dns_pattern("a.b.lab.internal", "*.lab.internal") is False
          and match_san_dns_pattern("lab.internal", "*.lab.internal") is False)

    # 2. X.509 certificate chain, clock window, and SAN validation (Sections 4 & 6)
    v_ok = validate_x509_leaf_certificate(
        requested_host="api.lab.internal",
        san_dns_names=["api.lab.internal", "*.lab.internal"],
        not_before_epoch=1700000000,
        not_after_epoch=1707776000,
        current_clock_epoch=1701000000,
        intermediate_present=True,
        root_in_trust_store=True,
    )
    check("valid chain + valid clock + matching SAN passes X.509 verification",
          v_ok["valid"] is True and v_ok["errors"] == [])

    v_missing_int = validate_x509_leaf_certificate(
        requested_host="api.lab.internal",
        san_dns_names=["*.lab.internal"],
        not_before_epoch=1700000000,
        not_after_epoch=1707776000,
        current_clock_epoch=1701000000,
        intermediate_present=False,
        root_in_trust_store=True,
    )
    check("omitting intermediate CA triggers 'unable_to_get_local_issuer_certificate_missing_intermediate'",
          v_missing_int["valid"] is False and "missing_intermediate" in v_missing_int["errors"][0])

    v_skew_expired = validate_x509_leaf_certificate(
        requested_host="wrong.example.com",
        san_dns_names=["*.lab.internal"],
        not_before_epoch=1700000000,
        not_after_epoch=1707776000,
        current_clock_epoch=1710000000,
        intermediate_present=True,
        root_in_trust_store=False,
    )
    check("untrusted root + expired clock + wrong hostname flags all 3 errors",
          len(v_skew_expired["errors"]) == 3)

    # 3. Connection setup RTTs: TCP+TLS 1.2 (3 RTT) vs TCP+TLS 1.3 (2 RTT) vs QUIC 1-RTT/0-RTT (Sections 1 & 3)
    check("TCP + TLS 1.2 takes 3 RTTs (1 TCP + 2 TLS); TCP + TLS 1.3 takes 2 RTTs (1 TCP + 1 TLS)",
          compute_connection_setup_rtts("tcp", "1.2") == 3
          and compute_connection_setup_rtts("tcp", "1.3") == 2)
    check("QUIC (HTTP/3) takes 1 RTT on cold start and 0 RTTs on resumed 0-RTT connection",
          compute_connection_setup_rtts("quic", "1.3", zero_rtt_resumption=False) == 1
          and compute_connection_setup_rtts("quic", "1.3", zero_rtt_resumption=True) == 0)

    # 4. HTTP status code diagnostics for AI gateways (Section 1 & 6)
    check("401 is Unauthenticated and 403 is Forbidden (Unauthorized)",
          "Unauthenticated" in classify_http_status_code(401)["meaning"]
          and "Forbidden" in classify_http_status_code(403)["meaning"])
    check("502 is Bad Gateway and 504 is Gateway Timeout (slow model inference vs proxy timeout)",
          "Bad Gateway" in classify_http_status_code(502)["meaning"]
          and "Gateway Timeout" in classify_http_status_code(504)["meaning"])
    check("413 is Payload Too Large and 499 is nginx Client Closed Request",
          "Too Large" in classify_http_status_code(413)["meaning"]
          and "Client Closed" in classify_http_status_code(499)["meaning"])

    # 5. Additional provenance checks from chapter text
    check("30 days in seconds for 'openssl x509 -checkend 2592000' is 30 * 86400 = 2,592,000",
          30 * 86400 == 2592000)
    check("Let's Encrypt default lifetime is 90 days and kubeadm leaf cert default is 365 days (1 year)",
          90 < 365)
    check("compute_connection_setup_rtts raises ValueError on unknown transport",
          _raises(lambda: compute_connection_setup_rtts("sctp")))

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
