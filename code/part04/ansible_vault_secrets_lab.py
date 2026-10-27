#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.12: Ansible Vault and secrets management."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_vault_secrets import (
    TwoPhaseSecretRotator,
    can_decrypt_vault_blob,
    parse_ansible_vault_header,
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
    # 1. Section 2 & 6: $ANSIBLE_VAULT header validation and pre-commit plaintext rejection
    h11 = parse_ansible_vault_header("$ANSIBLE_VAULT;1.1;AES256")
    h12 = parse_ansible_vault_header("$ANSIBLE_VAULT;1.2;AES256;prod")
    plaintext_rejected = False
    try:
        parse_ansible_vault_header("vault_db_password: plaintext_secret")
    except ValueError:
        plaintext_rejected = True
    check(
        "parse_ansible_vault_header parses 1.1 and 1.2;prod headers and rejects unencrypted vault files",
        h11 == {"format_version": "1.1", "cipher": "AES256", "vault_id": None}
        and h12 == {"format_version": "1.2", "cipher": "AES256", "vault_id": "prod"}
        and plaintext_rejected is True,
    )

    # 2. Section 2 & AUR Ch. 10: Vault ID environment isolation (dev key cannot decrypt prod vault)
    prod_header = "$ANSIBLE_VAULT;1.2;AES256;prod"
    dev_only = {"dev": "dev-pass"}
    dev_and_prod = {"dev": "dev-pass", "prod": "prod-pass"}
    check(
        "dev-only vault credentials cannot decrypt prod vault; prod vault-id succeeds",
        can_decrypt_vault_blob(prod_header, dev_only, "prod", "prod-pass") is False
        and can_decrypt_vault_blob(prod_header, dev_and_prod, "prod", "prod-pass") is True,
    )

    # 3. Section 7: Two-phase zero-downtime credential rotation (blocks premature revocation)
    rot = TwoPhaseSecretRotator("key_v1", ["app01", "app02"])
    rot.add_new_provider_key("key_v2")
    rot.update_consumer("app01", "key_v2")
    premature_blocked = False
    try:
        rot.revoke_old_provider_key("key_v1")  # app02 still on key_v1!
    except RuntimeError:
        premature_blocked = True
    rot.update_consumer("app02", "key_v2")
    revoked_ok = rot.revoke_old_provider_key("key_v1")
    check(
        "TwoPhaseSecretRotator blocks revoking key_v1 while app02 uses it, then revokes cleanly after all consumers upgrade",
        premature_blocked is True and revoked_ok is True and rot.provider_valid_keys == {"key_v2"},
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
