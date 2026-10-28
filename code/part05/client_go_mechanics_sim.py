"""Chapter 5.30 model: `apimachinery` `resource.Quantity` (binary `Ki..Ei` vs
decimal `n..E`) & `intstr.GetScaledValueFromIntOrPercent` calculator (`KPG`
Ch. 4), `runtime.Scheme` & `meta.DefaultRESTMapper` (`GVK` <-> `GVR`, `KPG`
Ch. 5), and `client-go` Lister cache `DeepCopy()` immutability guard (`KPG`
Ch. 6 & 7, `NPA` Ch. 7).

Sources modeled:
- Philippe Martin, Kubernetes Programming with Go (kubernetes-programming-with-
  go-programming-kubernetes-clients-and-operators-using-go-and-the-kuberne, KPG),
  Chapters 4, 5, 6, and 7:
  * Chapter 4 ("Using Common Types"): `pointer.Int32` / `ptr.To`, `Int32Deref`,
    `resource.Quantity` binary (`Ki`, `Mi`, `Gi`, `Ti`, `Pi`, `Ei`) vs decimal
    (`n`, `u`, `m`, `k`, `M`, `G`, `T`, `P`, `E`) suffixes, `intstr.IntOrString`
    & `GetScaledValueFromIntOrPercent`, `metav1.Time`.
  * Chapter 5 ("The API Machinery"): `schema.GroupVersionKind` (`GVK`) vs
    `schema.GroupVersionResource` (`GVR`), `runtime.Scheme` (`AddKnownTypes`,
    `ObjectKinds`, `New`, `Convert`), `meta.DefaultRESTMapper` (`RESTMapping`,
    `KindFor`, `ResourceFor`), and JSON/YAML/Protobuf serializers.
  * Chapter 6 ("The Client-go Library"): `rest.Config` (`QPS`, `Burst`,
    `NewTokenBucketRateLimiter`), `labels.NewRequirement`, `fields.OneTermEqualSelector`,
    `ApplyConfigurations`, `SharedInformerFactory`, `Lister` `DeepCopy()`, and
    `workqueue`.
  * Chapter 7 ("Testing Applications Using Client-go"): `fake.NewSimpleClientset`,
    `Actions()`, `PrependReactor`, and `fakediscovery.FakeDiscovery`.
- Jason Edelman, Scott S. Lowe & Matt Oswalt, Network Programmability and
  Automation, 2nd ed. (network-programmability-and-automation-2nd-edition, NPA),
  Chapter 7 ("Go": pointer vs value receivers, interfaces, goroutines/channels,
  `net/netip` `ParsePrefix`, `regexp`).
"""
import copy
import math
import re
from typing import Any, Callable, Dict, List, Mapping, Tuple

BINARY_SUFFIXES: Dict[str, int] = {
    "Ki": 2**10,
    "Mi": 2**20,
    "Gi": 2**30,
    "Ti": 2**40,
    "Pi": 2**50,
    "Ei": 2**60,
}

DECIMAL_MILLI_SUFFIXES: Dict[str, int] = {
    "m": 1,
    "": 1000,
    "k": 1000 * (10**3),
    "M": 1000 * (10**6),
    "G": 1000 * (10**9),
    "T": 1000 * (10**12),
}

QUANTITY_RE = re.compile(r"^([0-9]+(?:\.[0-9]+)?)(Ki|Mi|Gi|Ti|Pi|Ei|m|k|M|G|T)?$")


def parse_k8s_quantity_milli(q_str: str) -> int:
    """Model KPG Ch. 4 `resource.MustParse(q_str).MilliValue()`."""
    m = QUANTITY_RE.match(q_str.strip())
    if not m:
        raise ValueError(f"invalid resource.Quantity {q_str!r}")
    num_str, suffix = m.group(1), m.group(2) or ""
    val = float(num_str)
    if suffix in BINARY_SUFFIXES:
        return int(round(val * BINARY_SUFFIXES[suffix] * 1000))
    return int(round(val * DECIMAL_MILLI_SUFFIXES[suffix]))


def get_scaled_value_from_int_or_percent(
    int_or_pct: int | str,
    total: int,
    round_up: bool = True,
) -> int:
    """Model KPG Ch. 4 `intstr.GetScaledValueFromIntOrPercent`."""
    if isinstance(int_or_pct, int):
        return int_or_pct
    s = str(int_or_pct).strip()
    if s.endswith("%"):
        pct = float(s[:-1]) / 100.0
        raw = total * pct
        return int(math.ceil(raw)) if round_up else int(math.floor(raw))
    return int(s)


class DefaultRESTMapperSim:
    """Model KPG Ch. 5 `meta.DefaultRESTMapper` mapping `GVK <-> GVR`."""

    def __init__(self) -> None:
        self.gvk_to_gvr: Dict[Tuple[str, str, str], Tuple[str, str, str, str]] = {}
        self.gvr_to_gvk: Dict[Tuple[str, str, str], Tuple[str, str, str, str]] = {}

    @staticmethod
    def _pluralize(kind: str) -> str:
        w = kind.lower()
        if w.endswith(("s", "x", "z", "ch", "sh")):
            return w + "es"
        if w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
            return w[:-1] + "ies"
        return w + "s"

    def add(self, group: str, version: str, kind: str, scope: str = "Namespaced") -> None:
        plural = self._pluralize(kind)
        gvk = (group, version, kind)
        gvr = (group, version, plural)
        self.gvk_to_gvr[gvk] = (group, version, plural, scope)
        self.gvr_to_gvk[gvr] = (group, version, kind, scope)


class FakeClientsetWithCacheSim:
    """Model KPG Ch. 6 & 7 SharedInformer Lister cache (`DeepCopy` requirement)
    and `fake.NewSimpleClientset` `PrependReactor` + `Actions()` recording.
    """

    def __init__(self, initial_nodes: Mapping[str, Mapping[str, Any]]) -> None:
        self._cache: Dict[str, Dict[str, Any]] = copy.deepcopy(dict(initial_nodes))
        self.actions: List[Tuple[str, str, str]] = []
        self.reactors: List[Tuple[str, str, Callable[[str, Dict[str, Any]], Tuple[bool, Exception | None]]]] = []

    def lister_get(self, name: str, *, deep_copy: bool = False) -> Dict[str, Any]:
        obj = self._cache[name]
        return copy.deepcopy(obj) if deep_copy else obj

    def prepend_reactor(
        self,
        verb: str,
        resource: str,
        fn: Callable[[str, Dict[str, Any]], Tuple[bool, Exception | None]],
    ) -> None:
        self.reactors.insert(0, (verb, resource, fn))

    def patch_node(self, name: str, patch_fields: Mapping[str, Any]) -> None:
        self.actions.append(("patch", "nodes", name))
        for r_verb, r_res, fn in self.reactors:
            if r_verb in {"*", "patch"} and r_res in {"*", "nodes"}:
                handled, err = fn(name, dict(patch_fields))
                if handled:
                    if err is not None:
                        raise err
                    return
        self._cache[name].update(copy.deepcopy(dict(patch_fields)))
