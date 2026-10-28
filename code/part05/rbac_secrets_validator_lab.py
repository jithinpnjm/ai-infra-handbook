#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.16: Configuration, secrets and RBAC."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rbac_secrets_validator import (
    evaluate_rbac_and_audit_escalations,
    simulate_etcd_encryption_key_rotation,
    validate_configmap_or_secret_key,
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
    # 1. KUR Ch. 13 Table 13-1: ConfigMap and Secret key naming rules
    valid_keys = [".auth_token", "Key.pem", "config_file"]
    invalid_keys = ["Token..properties", "auth file.json", "_password.txt"]
    check(
        "validate_configmap_or_secret_key acceptsKUR Table 13-1 valid keys (.auth_token, Key.pem, config_file) and rejects invalid keys (Token..properties, auth file.json, _password.txt)",
        all(validate_configmap_or_secret_key(k)[0] for k in valid_keys)
        and all(not validate_configmap_or_secret_key(k)[0] for k in invalid_keys),
    )

    # 2. PK Ch. 7: EncryptionConfiguration key rotation (keeping secret-key-1 while promoting secret-key-2)
    etcd_state = {"login1": "identity", "login2": "secret-key-1"}
    safe_rot = simulate_etcd_encryption_key_rotation(
        ["secret-key-2", "secret-key-1", "identity"],
        etcd_state,
    )
    broken_rot = simulate_etcd_encryption_key_rotation(
        ["secret-key-2", "identity"],  # prematurely removed secret-key-1 before kubectl replace!
        etcd_state,
    )
    check(
        "EncryptionConfiguration rotation uses secret-key-2 for new writes, reads secret-key-1 when kept, and fails if secret-key-1 is removed before re-encryption",
        safe_rot["new_write_key"] == "secret-key-2"
        and safe_rot["unreadable_secrets"] == []
        and len(broken_rot["unreadable_secrets"]) == 1,
    )

    # 3. KUR Ch. 14 & PK Ch. 10: RBAC impersonation sudo workflow & escalation audit
    bindings = [
        {
            "name": "cluster-admin-view",
            "namespace": None,
            "role_name": "view",
            "subjects": [{"kind": "Group", "name": "ops-team"}],
            "rules": [{"resources": ["pods", "configmaps"], "verbs": ["get", "list", "watch"]}],
        },
        {
            "name": "cluster-admin-impersonate",
            "namespace": None,
            "role_name": "cluster-admin-impersonator",
            "subjects": [{"kind": "Group", "name": "ops-team"}],
            "rules": [{"resources": ["users"], "verbs": ["impersonate"], "resourceNames": ["cluster-admin"]}],
        },
    ]
    can_create_direct, _ = evaluate_rbac_and_audit_escalations(
        bindings, user="john", groups={"ops-team"}, namespace="default", verb="create", resource="configmaps"
    )
    can_impersonate_admin, _ = evaluate_rbac_and_audit_escalations(
        bindings, user="john", groups={"ops-team"}, namespace="", verb="impersonate", resource="users", resource_name="cluster-admin"
    )
    can_impersonate_other, _ = evaluate_rbac_and_audit_escalations(
        bindings, user="john", groups={"ops-team"}, namespace="", verb="impersonate", resource="users", resource_name="jane"
    )
    check(
        "RBAC sudo workflow denies direct configmap create to 'john', allows impersonating 'cluster-admin', and blocks impersonating 'jane'",
        can_create_direct is False and can_impersonate_admin is True and can_impersonate_other is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
