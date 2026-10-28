"""Chapter 5.29 model: CRD structural schema pruner, defaulter, and
`x-kubernetes-validations` CEL evaluator (`self == oldSelf` immutability &
cross-field rule), hub-and-spoke multi-version conversion + `storedVersions`
migrator, and operator finalizer + `/status` subresource reconciler (`KUR` Ch.
17 & 18, `PK` Ch. 11 & 16, `KPG`, `bcm11-containerization` Ch. 6).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapters
  17 ("Extending Kubernetes") & 18 ("Accessing Kubernetes from Common
  Programming Languages": OpenAPI spec >4 MB, `kubectl --v=10`, Python
  `config.load_kube_config()` vs `load_incluster_config()`, `CoreV1Api`,
  `AppsV1Api`, `watch.Watch().stream`, `stream(connect_get_namespaced_pod_exec)`,
  and `portforward(connect_get_namespaced_pod_portforward)`).
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 11 & 16.
- Philippe Martin / Stefan Schimanski & Michael Hausenblas, Kubernetes
  Programming with Go / Programming Kubernetes (kubernetes-programming-with-go-
  programming-kubernetes-clients-and-operators-using-go-and-the-kuberne, KPG).
- NVIDIA Base Command Manager 11 Containerization Manual (bcm11-containerization,
  Chapter 6: "Kubernetes Operators").
"""
from typing import Any, Dict, List, Mapping, Set, Tuple


def evaluate_crd_schema_and_cel(
    incoming_spec: Mapping[str, Any],
    old_spec: Mapping[str, Any] | None = None,
) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Model Section 2 `GPUHealthPolicy` structural schema pruning, defaulting,
    enum/range validation, and `x-kubernetes-validations` CEL rules:
    - Prunes unknown fields not in `{"nodeSelector", "xid", "maxUnavailableNodes", "targetPool"}`.
    - Defaults `xid.action = "Cordon"` and `xid.windowSeconds = 600`.
    - Validates `xid.action in {"Ignore", "Cordon", "CordonAndDrain"}` and
      `1 <= code <= 200`.
    - CEL cross-field rule: `self.xid.action != 'CordonAndDrain' || has(self.maxUnavailableNodes)`.
    - CEL immutability rule: `targetPool` (if set) must satisfy `self.targetPool == oldSelf.targetPool`.
    """
    allowed_top_keys = {"nodeSelector", "xid", "maxUnavailableNodes", "targetPool"}
    pruned: Dict[str, Any] = {k: v for k, v in incoming_spec.items() if k in allowed_top_keys}
    errors: List[str] = []

    if "xid" not in pruned or not isinstance(pruned["xid"], Mapping):
        return False, pruned, ["spec.xid is required"]

    xid = dict(pruned["xid"])
    xid.setdefault("action", "Cordon")
    xid.setdefault("windowSeconds", 600)
    pruned["xid"] = xid

    codes = xid.get("codes", [])
    if not codes:
        errors.append("spec.xid.codes must have minItems >= 1")
    for c in codes:
        if not (1 <= int(c) <= 200):
            errors.append(f"spec.xid.codes item {c} out of range 1..200")

    if xid["action"] not in {"Ignore", "Cordon", "CordonAndDrain"}:
        errors.append(f"invalid spec.xid.action {xid['action']!r}")

    # CEL cross-field rule
    if xid["action"] == "CordonAndDrain" and "maxUnavailableNodes" not in pruned:
        errors.append("CEL validation failed: maxUnavailableNodes is required when action is CordonAndDrain")

    # CEL immutability rule on targetPool
    if old_spec is not None and "targetPool" in old_spec:
        if pruned.get("targetPool") != old_spec.get("targetPool"):
            errors.append("CEL validation failed: spec.targetPool is immutable (self == oldSelf)")

    return (len(errors) == 0), pruned, errors


def convert_crd_via_hub_and_migrate_storage(
    objects_in_etcd: List[Dict[str, Any]],
    new_storage_version: str = "v1beta1",
) -> Dict[str, Any]:
    """Model Section 2 Hub-and-Spoke conversion (`v1alpha1` <-> Hub `v1beta1`)
    and storage version migration updating `status.storedVersions`.
    In `v1alpha1`, field was `xidCodes: [48, 79]`; in `v1beta1` (Hub), it is
    structured as `xid: {"codes": [48, 79]}`.
    """
    migrated: List[Dict[str, Any]] = []
    for obj in objects_in_etcd:
        doc = dict(obj)
        if doc.get("apiVersion", "").endswith("/v1alpha1"):
            codes = doc.pop("xidCodes", [])
            doc["apiVersion"] = f"platform.example.com/{new_storage_version}"
            doc["xid"] = {"codes": list(codes)}
        migrated.append(doc)

    stored_versions: Set[str] = {d["apiVersion"].split("/")[-1] for d in migrated}
    return {
        "migrated_objects": migrated,
        "stored_versions": sorted(stored_versions),
    }


def reconcile_cr_with_finalizer_and_status(
    cr: Dict[str, Any],
    *,
    finalizer_name: str = "platform.example.com/cleanup",
) -> Dict[str, str]:
    """Model Section 2 & 3 operator finalizer lifecycle and `/status` subresource
    update (which updates `status.observedGeneration` without incrementing
    `metadata.generation`).
    """
    meta = cr.setdefault("metadata", {})
    finalizers: List[str] = list(meta.get("finalizers", []))
    gen = int(meta.get("generation", 1))

    if meta.get("deletionTimestamp"):
        if finalizer_name in finalizers:
            finalizers.remove(finalizer_name)
            meta["finalizers"] = finalizers
            return {"action": "cleaned_up_external_and_removed_finalizer", "can_delete_from_etcd": str(len(finalizers) == 0)}
        return {"action": "noop_already_cleaned", "can_delete_from_etcd": "True"}

    if finalizer_name not in finalizers:
        finalizers.append(finalizer_name)
        meta["finalizers"] = finalizers

    # Status subresource update: does NOT increment metadata.generation!
    status = cr.setdefault("status", {})
    status["observedGeneration"] = gen
    status["ready"] = "True"
    return {"action": "reconciled_and_updated_status", "generation": str(gen), "observedGeneration": str(status["observedGeneration"])}
