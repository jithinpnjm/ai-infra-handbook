"""Chapter 2.10 model: X.509 certificate chain, validity window, and RFC 6125
Subject Alternative Name (SAN) wildcard matching validator, TLS + TCP handshake
RTT cost calculator (HTTP/1.1 vs HTTP/2 vs HTTP/3 QUIC 1-RTT/0-RTT), and HTTP
gateway/client status code classifier.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 10 ("Transport Security": integrity, confidentiality, authentication,
  data-exhaust privacy, symmetric vs public-key, Diffie-Hellman forward secrecy,
  hashes/MACs, Web of Trust vs Hierarchical CA PKI, MitM, MAC randomization,
  onion routing, TLS handshake).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 10
  (network applications, public-key authentication, host keys).
- Josh Rosso et al., Production Kubernetes (PK), Chapter 6 (Ingress / Gateway
  TLS termination, re-encryption, passthrough, cert-manager).
"""
from typing import Dict, List


def match_san_dns_pattern(hostname: str, san_pattern: str) -> bool:
    """Match a DNS hostname against an X.509 SAN entry per RFC 6125 (wildcard '*' matches a single leftmost label)."""
    h = hostname.strip().lower().rstrip(".")
    p = san_pattern.strip().lower().rstrip(".")
    if not p.startswith("*."):
        return h == p
    suffix = p[2:]  # e.g. 'lab.internal'
    if "." not in h:
        return False
    first_label, rest = h.split(".", 1)
    return bool(first_label) and rest == suffix


def validate_x509_leaf_certificate(
    requested_host: str,
    san_dns_names: List[str],
    not_before_epoch: int,
    not_after_epoch: int,
    current_clock_epoch: int,
    intermediate_present: bool,
    root_in_trust_store: bool,
) -> Dict[str, object]:
    """Validate an X.509 leaf certificate's chain, clock window, and SAN hostname match."""
    errors: List[str] = []
    if not root_in_trust_store:
        errors.append("unknown_authority_root_not_trusted")
    if not intermediate_present:
        errors.append("unable_to_get_local_issuer_certificate_missing_intermediate")
    if current_clock_epoch < not_before_epoch:
        errors.append("certificate_not_yet_valid_clock_skew")
    elif current_clock_epoch > not_after_epoch:
        errors.append("certificate_has_expired")
    if not any(match_san_dns_pattern(requested_host, pat) for pat in san_dns_names):
        errors.append("hostname_mismatch_not_in_san")
    return {"valid": len(errors) == 0, "errors": errors}


def compute_connection_setup_rtts(
    transport: str,
    tls_version: str = "1.3",
    zero_rtt_resumption: bool = False,
) -> int:
    """Compute round trips (RTTs) before the first HTTP request byte can be sent on a cold connection."""
    if transport == "tcp":
        tcp_rtts = 1
        if tls_version == "none":
            tls_rtts = 0
        elif tls_version == "1.3":
            tls_rtts = 0 if zero_rtt_resumption else 1
        elif tls_version == "1.2":
            tls_rtts = 2
        else:
            raise ValueError(f"Unsupported tls_version: {tls_version}")
        return tcp_rtts + tls_rtts
    if transport == "quic":
        return 0 if zero_rtt_resumption else 1
    raise ValueError(f"Unsupported transport: {transport}")


def classify_http_status_code(status_code: int) -> Dict[str, str]:
    """Classify key HTTP status codes for AI serving and gateway diagnostics."""
    mapping = {
        200: {"category": "2xx_success", "meaning": "OK"},
        304: {"category": "3xx_redirect_cache", "meaning": "Not Modified (ETag/Cache-Control hit)"},
        401: {"category": "4xx_client_auth", "meaning": "Unauthenticated (missing/invalid credentials)"},
        403: {"category": "4xx_client_authz", "meaning": "Forbidden (authenticated but unauthorized by policy)"},
        413: {"category": "4xx_client_size", "meaning": "Payload Too Large (exceeded proxy client_max_body_size)"},
        429: {"category": "4xx_client_rate", "meaning": "Too Many Requests (rate limited)"},
        499: {"category": "4xx_client_closed", "meaning": "Client Closed Request before upstream responded (nginx)"},
        502: {"category": "5xx_upstream_bad", "meaning": "Bad Gateway (upstream reset, refused, or invalid response)"},
        503: {"category": "5xx_upstream_unavail", "meaning": "Service Unavailable (no healthy upstream endpoints)"},
        504: {"category": "5xx_upstream_timeout", "meaning": "Gateway Timeout (upstream model inference exceeded proxy read timeout)"},
    }
    return mapping.get(status_code, {"category": f"{status_code // 100}xx", "meaning": "Other"})
