"""Chapter 5.7 model: Pod QoS class (`Guaranteed` / `Burstable` / `BestEffort`)
and `oom_score_adj` calculator, effective Pod scheduling request calculator with
init containers (`max(max_init, sum_app)`), and Kubernetes label key/value
syntax validator (`KUR` Ch. 5 & 6, `PK` Ch. 14).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapters
  4, 5, 6, 9–12, and 22:
  * Chapter 5 ("Pods"): Pod co-scheduling ("What should I put in a Pod?"),
    `emptyDir` and `nfs` volumes, resource requests vs limits (`400m` = 0.4 cores
    vs `400Mi` memory), liveness/readiness probes.
  * Chapter 6 ("Labels and Annotations"): 253-char DNS subdomain prefix + `/` +
    63-char `[a-zA-Z0-9]`-bounded key/value syntax, equality and set-based
    selectors (`app in (alpaca,bandicoot)`, `ver=2,!canary`).
  * Chapter 22 ("Organizing Your Application"): filesystem in Git as source of
    truth (`etcd` is a reflection), PR code review, `Development -> Staging ->
    Canary -> Production` & regional rollout order, and Helm templates.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 14 ("Application Considerations"):
  * ConfigMaps/Secrets vs Vault, Downward API (`MEM_LIMIT` via `resourceFieldRef`),
    `SIGTERM` graceful shutdown (`signal.Notify`) + `preStop` hook, liveness vs
    readiness probes, and Prometheus `/metrics` + OpenTracing/Jaeger spans.
"""
import re
from typing import Any, Dict, List, Mapping, Sequence, Tuple

DNS_SUBDOMAIN_RE = re.compile(r"^[a-z0-9]([-a-z0-9]*[a-z0-9])?(\.[a-z0-9]([-a-z0-9]*[a-z0-9])?)*$")
LABEL_NAME_RE = re.compile(r"^[A-Za-z0-9]([-A-Za-z0-9_.]*[A-Za-z0-9])?$")


def compute_pod_qos_and_effective_requests(
    init_containers: Sequence[Mapping[str, Mapping[str, int]]],
    app_containers: Sequence[Mapping[str, Mapping[str, int]]],
    node_memory_mi: int = 512_000,
) -> Dict[str, Any]:
    """Compute Pod QoS class (`Guaranteed`, `Burstable`, `BestEffort`),
    `oom_score_adj`, and effective Pod scheduling requests:
      effective_request(res) = max(max_init(res), sum_app(res)).
    Each container mapping has `requests: {cpu_m, mem_mi, gpu}` and
    `limits: {cpu_m, mem_mi, gpu}`.
    """
    all_ctrs = list(init_containers) + list(app_containers)
    any_req_or_lim = False
    all_guaranteed = True

    for ctr in all_ctrs:
        req = ctr.get("requests", {})
        lim = ctr.get("limits", {})
        if any(v > 0 for v in req.values()) or any(v > 0 for v in lim.values()):
            any_req_or_lim = True
        cpu_req, cpu_lim = int(req.get("cpu_m", 0)), int(lim.get("cpu_m", 0))
        mem_req, mem_lim = int(req.get("mem_mi", 0)), int(lim.get("mem_mi", 0))
        if cpu_req <= 0 or mem_req <= 0 or cpu_req != cpu_lim or mem_req != mem_lim:
            all_guaranteed = False

    if not any_req_or_lim:
        qos = "BestEffort"
        oom_score_adj = 1000
    elif all_guaranteed:
        qos = "Guaranteed"
        oom_score_adj = -997
    else:
        qos = "Burstable"
        total_mem_req = sum(int(c.get("requests", {}).get("mem_mi", 0)) for c in app_containers)
        oom_score_adj = max(2, min(999, 1000 - int(1000 * total_mem_req / max(1, node_memory_mi))))

    eff_req: Dict[str, int] = {}
    for res in ("cpu_m", "mem_mi", "gpu"):
        max_init = max((int(c.get("requests", {}).get(res, 0)) for c in init_containers), default=0)
        sum_app = sum(int(c.get("requests", {}).get(res, 0)) for c in app_containers)
        eff_req[res] = max(max_init, sum_app)

    return {
        "qos_class": qos,
        "oom_score_adj": oom_score_adj,
        "effective_requests": eff_req,
    }


def validate_k8s_label(key: str, value: str) -> Tuple[bool, List[str]]:
    """Model Section 1 & KUR Ch. 6 Kubernetes label key and value syntax rules."""
    errors: List[str] = []
    if "/" in key:
        prefix, name = key.split("/", 1)
        if not prefix or len(prefix) > 253 or not DNS_SUBDOMAIN_RE.match(prefix):
            errors.append(f"invalid label prefix {prefix!r} (must be DNS subdomain <= 253 chars)")
    else:
        name = key

    if not name or len(name) > 63 or not LABEL_NAME_RE.match(name):
        errors.append(f"invalid label name {name!r} (must be 1..63 chars, start/end alphanumeric)")

    if value != "" and (len(value) > 63 or not LABEL_NAME_RE.match(value)):
        errors.append(f"invalid label value {value!r} (must be 0..63 chars, start/end alphanumeric)")

    return (len(errors) == 0), errors
