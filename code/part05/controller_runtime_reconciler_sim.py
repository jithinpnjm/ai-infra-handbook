"""Chapter 5.31 model: `controller-runtime` `GenerationChangedPredicate` & Node
heartbeat predicate filter (`KPG` Ch. 10), `meta.SetStatusCondition` transition
timestamp & no-op status patch guard (`KPG` Ch. 11), and Kubebuilder Hub-and-Spoke
`ConvertTo`/`ConvertFrom` + `FieldIndexer` (`KPG` Ch. 9, 10, 12, 13 & `PK` Ch. 8, 11).

Sources modeled:
- Philippe Martin / Stefan Schimanski & Michael Hausenblas, Kubernetes
  Programming with Go / Programming Kubernetes (kubernetes-programming-with-go-
  programming-kubernetes-clients-and-operators-using-go-and-the-kuberne, KPG),
  Chapters 9, 10, 11, 12, and 13:
  * Chapter 9 ("Working with Custom Resources"): `unstructured.Unstructured`
    nested helpers, `runtime.DefaultUnstructuredConverter`, `+k8s:deepcopy-gen`,
    and `+genclient` (`client-gen`).
  * Chapter 10 ("Writing Operators with the Controller-Runtime Library"):
    `Manager`, `Client` (cached reads vs direct writes), `Patch(ctx, obj, client.Apply, client.FieldOwner(...))`,
    `Builder` (`ControllerManagedBy`, `For`, `Owns`, `Watches`), `predicate.Funcs`
    & `GenerationChangedPredicate`, `log.FromContext(ctx)`, and `EventRecorder`.
  * Chapter 11 ("Writing the Reconcile Loop"): `Reconcile` (`Result{}`,
    `Result{RequeueAfter: d}`, error backoff), `applyDeployment` with Server-Side
    Apply, and `computeStatus` updating `/status`.
  * Chapter 12 ("Testing the Reconcile Loop"): `setup-envtest`, `envtest.Environment`
    (`CRDDirectoryPaths`, `ErrorIfCRDPathMissing`), Ginkgo/Gomega `Eventually`.
  * Chapter 13 ("Creating an Operator with Kubebuilder"): `kubebuilder init`,
    `kubebuilder create api`, `+kubebuilder:rbac` / `+kubebuilder:subresource:status`,
    multi-version Hub (`func (*MyResource) Hub() {}`) and Spoke (`ConvertTo`,
    `ConvertFrom`), and `kubebuilder create webhook --conversion`.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 8 & 11.
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def evaluate_watch_predicates(
    old_obj: Mapping[str, Any],
    new_obj: Mapping[str, Any],
    *,
    is_primary_cr: bool = True,
) -> bool:
    """Model Section 5 & KPG Ch. 10 Predicates:
    - For primary CR (`GenerationChangedPredicate`): returns True ONLY if
      `metadata.generation` changed (ignoring `/status`-only updates) or
      `deletionTimestamp` was set.
    - For secondary watched `Node`: ignores heartbeat-only updates where
      `spec.unschedulable`, `labels`, `annotations`, and condition `(type, status, reason)`
      tuples are unchanged.
    """
    if is_primary_cr:
        old_gen = int(old_obj.get("metadata", {}).get("generation", 1))
        new_gen = int(new_obj.get("metadata", {}).get("generation", 1))
        del_changed = bool(old_obj.get("metadata", {}).get("deletionTimestamp")) != bool(
            new_obj.get("metadata", {}).get("deletionTimestamp")
        )
        return (old_gen != new_gen) or del_changed

    # Node predicate: compare spec.unschedulable, labels, annotations, and conditions (ignoring heartbeat time)
    def node_decision_fingerprint(n: Mapping[str, Any]) -> Tuple[Any, ...]:
        conds = tuple(
            sorted(
                (c["type"], c["status"], c.get("reason", ""))
                for c in n.get("status", {}).get("conditions", ())
            )
        )
        return (
            bool(n.get("spec", {}).get("unschedulable", False)),
            tuple(sorted(n.get("metadata", {}).get("labels", {}).items())),
            tuple(sorted(n.get("metadata", {}).get("annotations", {}).items())),
            conds,
        )

    return node_decision_fingerprint(old_obj) != node_decision_fingerprint(new_obj)


def set_status_condition_and_check_noop(
    current_conditions: Sequence[Mapping[str, str]],
    new_cond: Mapping[str, str],
    now_iso: str,
) -> Tuple[bool, List[Dict[str, str]]]:
    """Model Section 4 `meta.SetStatusCondition` and no-op status write guard:
    - Only updates `lastTransitionTime` to `now_iso` if the condition `type` is
      new or its `status` (`True`/`False`/`Unknown`) changed.
    - Returns `(should_patch_status, updated_conditions)`.
    """
    updated: List[Dict[str, str]] = [dict(c) for c in current_conditions]
    target_type = new_cond["type"]
    found = False

    for c in updated:
        if c["type"] == target_type:
            found = True
            if c["status"] != new_cond["status"]:
                c["status"] = new_cond["status"]
                c["lastTransitionTime"] = now_iso
            c["reason"] = new_cond.get("reason", "")
            c["message"] = new_cond.get("message", "")
            break

    if not found:
        entry = dict(new_cond)
        entry["lastTransitionTime"] = now_iso
        updated.append(entry)

    should_patch = updated != [dict(c) for c in current_conditions]
    return should_patch, updated


def convert_myresource_spoke_to_hub_and_back(
    v1beta1_spoke: Mapping[str, Any],
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """Model KPG Ch. 13 Kubebuilder multi-version conversion between Spoke
    (`v1beta1` with `memoryRequest`) and Hub (`v1alpha1` with `memory`).
    """
    hub_v1alpha1 = {
        "apiVersion": "mygroup.myid.dev/v1alpha1",
        "kind": "MyResource",
        "metadata": dict(v1beta1_spoke.get("metadata", {})),
        "spec": {
            "image": v1beta1_spoke["spec"]["image"],
            "memory": v1beta1_spoke["spec"]["memoryRequest"],
        },
        "status": dict(v1beta1_spoke.get("status", {})),
    }
    roundtrip_v1beta1 = {
        "apiVersion": "mygroup.myid.dev/v1beta1",
        "kind": "MyResource",
        "metadata": dict(hub_v1alpha1["metadata"]),
        "spec": {
            "image": hub_v1alpha1["spec"]["image"],
            "memoryRequest": hub_v1alpha1["spec"]["memory"],
        },
        "status": dict(hub_v1alpha1["status"]),
    }
    return hub_v1alpha1, roundtrip_v1beta1
