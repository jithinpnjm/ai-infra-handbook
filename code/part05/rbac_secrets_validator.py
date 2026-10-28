"""Chapter 5.16 model: ConfigMap/Secret key syntax validator (`KUR` Ch. 13),
`EncryptionConfiguration` key-rotation simulator (`PK` Ch. 7), and RBAC
authorizer & dangerous privilege-escalation auditor (`KUR` Ch. 14 & `PK` Ch. 10).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapters
  13 & 14:
  * Chapter 13 ("ConfigMaps and Secrets"): key naming constraints (Table 13-1:
    may start with optional `.`, followed by alphanumeric, then `[-._a-zA-Z0-9]`,
    no `..` or spaces or leading `_`), `$(ENV_VAR)` command-line argument
    expansion, and live update via `kubectl create ... --dry-run=client -o yaml
    | kubectl replace -f -`.
  * Chapter 14 ("Role-Based Access Control for Kubernetes"): `Role` vs
    `ClusterRole`, `RoleBinding` vs `ClusterRoleBinding`, `kubectl auth can-i
    get pods --subresource=logs`, `rbac.authorization.kubernetes.io/autoupdate:
    "false"`, ClusterRole aggregation (`aggregate-to-edit`), and `kubectl auth
    reconcile -f`.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 7 ("Secret Management") & 10 ("Identity"):
  * Chapter 7: `EncryptionConfiguration` providers order (first provider encrypts
    new writes; all listed keys can decrypt existing etcd entries; removing an
    old key before re-encrypting causes `no matching key was found`), Vault
    Agent Injector & `secrets-store-csi-driver`.
  * Chapter 10: RBAC `impersonate` `sudo`-style admin workflow.
"""
import re
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple

CONFIG_KEY_RE = re.compile(r"^\.?[A-Za-z0-9]([-._A-Za-z0-9]*[A-Za-z0-9])?$")


def validate_configmap_or_secret_key(key: str) -> Tuple[bool, str]:
    """Model KUR Ch. 13 Table 13-1 ConfigMap and Secret key naming rules:
    - Valid: `.auth_token`, `Key.pem`, `config_file`
    - Invalid: `Token..properties` (contains `..`), `auth file.json` (space),
      `_password.txt` (starts with `_`).
    """
    if ".." in key:
        return False, "key cannot contain '..'"
    if not CONFIG_KEY_RE.match(key):
        return False, "key must start with optional dot + alphanumeric and contain only [-._A-Za-z0-9]"
    return True, "valid"


def simulate_etcd_encryption_key_rotation(
    active_keys_in_order: Sequence[str],
    secrets_in_etcd: Mapping[str, str],
) -> Dict[str, Any]:
    """Model PK Ch. 7 `EncryptionConfiguration` key rotation:
    - `active_keys_in_order[0]` is used to encrypt all new writes / `kubectl replace`
      operations.
    - Reading an existing secret encrypted with `key_x` succeeds ONLY if `key_x`
      is still present in `active_keys_in_order` (or `"identity"` for unencrypted).
    """
    write_key = active_keys_in_order[0]
    readable_keys = set(active_keys_in_order)
    unreadable: List[str] = []
    for sec_name, used_key in sorted(secrets_in_etcd.items()):
        if used_key not in readable_keys:
            unreadable.append(f"{sec_name}: unable to transform key (encrypted with {used_key!r}, not in {list(active_keys_in_order)})")
    return {
        "new_write_key": write_key,
        "unreadable_secrets": unreadable,
    }


def evaluate_rbac_and_audit_escalations(
    bindings: Sequence[Mapping[str, Any]],
    *,
    user: str,
    groups: Set[str],
    namespace: str,
    verb: str,
    resource: str,
    resource_name: str = "",
) -> Tuple[bool, List[str]]:
    """Evaluate additive RBAC rules and flag dangerous cluster-escalation patterns."""
    allowed = False
    escalation_warnings: List[str] = []

    for b in bindings:
        b_ns = b.get("namespace")  # None means ClusterRoleBinding
        subjects = b.get("subjects", [])
        rules = b.get("rules", [])

        for s in subjects:
            if s.get("name") in {"system:authenticated", "system:unauthenticated"} and b.get("role_name") == "cluster-admin":
                escalation_warnings.append(f"critical: {b['name']} binds cluster-admin to {s['name']}")

        for r in rules:
            res_list = r.get("resources", [])
            verbs_list = r.get("verbs", [])
            if "nodes/proxy" in res_list or "*" in res_list:
                if "*" in verbs_list or "create" in verbs_list or "get" in verbs_list:
                    escalation_warnings.append(f"high-privilege rule in {b['name']}: resources={res_list} verbs={verbs_list}")

        # Check if binding applies to caller and target namespace
        if b_ns is not None and b_ns != namespace:
            continue
        subj_match = any(
            (s.get("kind") == "User" and s.get("name") == user)
            or (s.get("kind") == "Group" and s.get("name") in groups)
            for s in subjects
        )
        if not subj_match:
            continue

        for r in rules:
            res_ok = "*" in r.get("resources", []) or resource in r.get("resources", [])
            verb_ok = "*" in r.get("verbs", []) or verb in r.get("verbs", [])
            rnames = r.get("resourceNames", [])
            name_ok = (not rnames) or (resource_name in rnames)
            if res_ok and verb_ok and name_ok:
                allowed = True

    return allowed, escalation_warnings
