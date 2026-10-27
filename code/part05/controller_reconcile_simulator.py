"""Chapter 5.6 model: Deduplicating rate-limited `WorkQueue`, level-triggered
`ReplicaSet` controller with label adoption & pod quarantining (`KUR` Ch. 9),
and budget-bounded GPU fault remediation controller (`Section 7`).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapters
  9–12 and 17:
  * Chapter 9 ("ReplicaSets"): reconciliation loops, decoupling Pods and
    ReplicaSets via label selectors, adopting existing containers, quarantining
    misbehaving containers by removing their label (`kubectl label pod ... app-`),
    and scaling (`kubectl scale` vs declarative YAML).
  * Chapter 10 ("Deployments"): `RollingUpdate` (`maxUnavailable`, `maxSurge`)
    vs `Recreate`, `rollout history --revision=2`, `rollout undo`.
  * Chapter 11 ("DaemonSets"): one pod per node (`fluentd`), nodeSelector
    (`ssd=true`), rolling updates.
  * Chapter 12 ("Jobs"): Job patterns (One-shot, Parallel fixed completions,
    Work queue with parallel consumers `memq` `keygen`), `restartPolicy: OnFailure`
    vs `Never`, `CronJob`.
- Philippe Martin, Kubernetes Programming with Go (kubernetes-programming-with-
  go-programming-kubernetes-clients-and-operators-using-go-and-the-kuberne, KPG),
  Chapters 3 & 6 (`OwnerReference`, `Controller: true`, `BlockOwnerDeletion: true`,
  SharedInformers, and WorkQueues).
"""
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


class DeduplicatingWorkQueue:
    """Model Section 2 client-go rate-limiting work queue:
    - Collapses multiple rapid events for the same `namespace/name` key into a
      single pending queue item (`dirty` set).
    - Guarantees that while a key is in `processing`, a concurrent event marks
      it `dirty` again without running two workers on the same key simultaneously.
    - Tracks exponential backoff retry count via `num_requeues`.
    """

    def __init__(self) -> None:
        self.queue: List[str] = []
        self.dirty: Set[str] = set()
        self.processing: Set[str] = set()
        self.requeue_counts: Dict[str, int] = {}

    def add(self, key: str) -> None:
        if key in self.dirty:
            return
        self.dirty.add(key)
        if key not in self.processing:
            self.queue.append(key)

    def get(self) -> str | None:
        if not self.queue:
            return None
        key = self.queue.pop(0)
        self.processing.add(key)
        self.dirty.discard(key)
        return key

    def done(self, key: str) -> None:
        self.processing.discard(key)
        if key in self.dirty:
            self.queue.append(key)

    def add_rate_limited(self, key: str, base_delay_sec: float = 1.0) -> float:
        count = self.requeue_counts.get(key, 0) + 1
        self.requeue_counts[key] = count
        self.add(key)
        return base_delay_sec * (2 ** (count - 1))

    def forget(self, key: str) -> None:
        self.requeue_counts.pop(key, None)


def reconcile_replicaset(
    rs_name: str,
    rs_uid: str,
    desired_replicas: int,
    selector_label: Tuple[str, str],
    pods: List[Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Model Section 3 & 4 and KUR Ch. 9 ReplicaSet level-triggered reconcile:
    1. Release (orphan) any pod whose `owner_uid == rs_uid` if it no longer
       matches `selector_label` (e.g. quarantined via `kubectl label pod ... app-`).
    2. Adopt any ownerless pod (`owner_uid is None`) whose labels match
       `selector_label`.
    3. Count owned matching pods; create missing pods or delete excess pods to
       converge to `desired_replicas`.
    """
    sel_k, sel_v = selector_label
    orphaned: List[str] = []
    adopted: List[str] = []
    created: List[str] = []
    deleted: List[str] = []

    for pod in pods:
        matches = pod.get("labels", {}).get(sel_k) == sel_v
        if pod.get("owner_uid") == rs_uid and not matches:
            pod["owner_uid"] = None
            orphaned.append(str(pod["name"]))
        elif pod.get("owner_uid") is None and matches:
            pod["owner_uid"] = rs_uid
            adopted.append(str(pod["name"]))

    active_owned = [p for p in pods if p.get("owner_uid") == rs_uid]
    diff = desired_replicas - len(active_owned)
    if diff > 0:
        for i in range(diff):
            new_name = f"{rs_name}-gen-{i + 1}"
            pods.append({"name": new_name, "labels": {sel_k: sel_v}, "owner_uid": rs_uid})
            created.append(new_name)
    elif diff < 0:
        for _ in range(-diff):
            victim = active_owned.pop()
            pods.remove(victim)
            deleted.append(str(victim["name"]))

    return {
        "orphaned": orphaned,
        "adopted": adopted,
        "created": created,
        "deleted": deleted,
        "active_owned": [str(p["name"]) for p in pods if p.get("owner_uid") == rs_uid],
    }


def reconcile_gpu_node_remediation(
    nodes: Sequence[Mapping[str, Any]],
    max_concurrent_cordons: int = 2,
) -> Dict[str, List[str]]:
    """Model Section 7 safe GPU fault remediation controller with a global
    blast-radius budget (`max_concurrent_cordons`).
    """
    already_cordoned = [str(n["name"]) for n in nodes if n.get("cordoned", False)]
    newly_cordoned: List[str] = []
    budget_deferred: List[str] = []

    current_cordoned_count = len(already_cordoned)
    for n in nodes:
        if n.get("cordoned", False):
            continue
        if n.get("sustained_xid_fault", False):
            if current_cordoned_count < max_concurrent_cordons:
                newly_cordoned.append(str(n["name"]))
                current_cordoned_count += 1
            else:
                budget_deferred.append(str(n["name"]))

    return {
        "already_cordoned": already_cordoned,
        "newly_cordoned": newly_cordoned,
        "budget_deferred": budget_deferred,
    }
