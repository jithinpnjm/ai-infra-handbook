"""Chapter 5.5 model: `etcd` MVCC revision store + `kube-apiserver` optimistic
concurrency (`409 Conflict`), watch stream with compaction (`410 Gone` and
`BOOKMARK`), Server-Side Apply (`managedFields`) field-ownership conflict
checker, and API Priority and Fairness (`APF`) concurrency-share allocator.

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 1 & 2.
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 17
  ("Extending Kubernetes"): custom resources (`LoadTest`), admission webhooks
  (`ValidatingWebhookConfiguration`, `MutatingWebhookConfiguration` returning
  base64 `JSONPatch`).
- Stefan Schimanski & Michael Hausenblas, Programming Kubernetes (kubernetes-
  programming-with-go-programming-kubernetes-clients-and-operators-using-go-and-
  the-kuberne, KPG), Chapter 2 ("Kubernetes API Operations").
- nvidia-devops (`volume-03/01-k8s-control-plane-scheduling-masterclass.md`).
"""
from typing import Any, Dict, List, Mapping, Tuple


class EtcdMVCCSimulator:
    """Model Section 3 & 7 etcd MVCC revisions, optimistic concurrency (409),
    compaction, and watch resume (410 Gone vs BOOKMARK).
    """

    def __init__(self) -> None:
        self.current_revision: int = 1
        self.compacted_revision: int = 1
        # key -> list of (revision, event_type, value_dict)
        self.history: Dict[str, List[Tuple[int, str, Dict[str, Any]]]] = {}
        self.latest: Dict[str, Tuple[int, Dict[str, Any]]] = {}

    def put(self, key: str, value: Mapping[str, Any], expected_rv: int | None = None) -> int:
        if expected_rv is not None:
            curr_rv = self.latest.get(key, (0, {}))[0]
            if curr_rv != expected_rv:
                raise RuntimeError(
                    f"409 Conflict: key {key!r} resourceVersion is {curr_rv}, expected {expected_rv}"
                )
        self.current_revision += 1
        rev = self.current_revision
        ev_type = "MODIFIED" if key in self.latest else "ADDED"
        doc = dict(value)
        doc["resourceVersion"] = str(rev)
        self.latest[key] = (rev, doc)
        self.history.setdefault(key, []).append((rev, ev_type, doc))
        return rev

    def compact(self, rev: int) -> None:
        if rev > self.current_revision:
            raise ValueError("cannot compact beyond current_revision")
        self.compacted_revision = max(self.compacted_revision, rev)

    def watch_from(self, key: str, start_rv: int, allow_bookmarks: bool = True) -> List[Tuple[int, str]]:
        if start_rv < self.compacted_revision:
            return [(self.compacted_revision, "ERROR: 410 Gone (too old resource version)")]
        events = [
            (r, ev)
            for (r, ev, _) in self.history.get(key, [])
            if r > start_rv
        ]
        if allow_bookmarks and not events:
            events.append((self.current_revision, "BOOKMARK"))
        return events


def evaluate_ssa_field_ownership(
    current_owners: Mapping[str, str],
    applying_manager: str,
    applied_fields: Mapping[str, Any],
    force_conflicts: bool = False,
) -> Tuple[bool, Dict[str, str], List[str]]:
    """Model Section 4 Server-Side Apply (`managedFields`) conflict detection."""
    updated_owners = dict(current_owners)
    conflicts: List[str] = []
    for field_path in sorted(applied_fields.keys()):
        existing_mgr = updated_owners.get(field_path)
        if existing_mgr is not None and existing_mgr != applying_manager:
            if not force_conflicts:
                conflicts.append(
                    f"409 Conflict on {field_path!r}: owned by {existing_mgr!r}, applied by {applying_manager!r}"
                )
            else:
                updated_owners[field_path] = applying_manager
        else:
            updated_owners[field_path] = applying_manager
    return (len(conflicts) == 0), updated_owners, conflicts


def compute_apf_concurrency_limit(
    server_total_concurrency: int,
    level_shares: Mapping[str, int],
) -> Dict[str, int]:
    """Model Section 6 API Priority and Fairness (`APF`) concurrency allocation
    proportional to `nominalConcurrencyShares`.
    """
    total_shares = sum(level_shares.values())
    return {
        name: round(server_total_concurrency * shares / total_shares)
        for name, shares in level_shares.items()
    }
