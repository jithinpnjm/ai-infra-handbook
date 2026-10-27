"""Chapter 4.12 model: `$ANSIBLE_VAULT;1.1;AES256` / `1.2` header parser &
pre-commit guard, `vault_identity_list` multi-environment password selector
(`dev@...` vs `prod@...`), and two-phase zero-downtime credential rotation
state machine.

Sources modeled:
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapter 10 ("Encryption at Rest"):
  * `ansible-vault` commands (`encrypt`, `decrypt`, `view`, `edit`, `rekey`,
    `create`, `encrypt_string`), `$ANSIBLE_VAULT;1.1;AES256` and
    `$ANSIBLE_VAULT;1.2;AES256;<vault-id>` header format, `--ask-vault-pass`,
    `--vault-password-file` (`chmod 0600` or executable client script), and
    `vault_identity_list = dev@~/.vault_dev, prod@~/.vault_prod` in `ansible.cfg`.
- volume-10/11-cicd-for-infrastructure-and-cluster-configuration.md (Vault,
  SOPS, BMC credentials, and secret leak prevention).
"""
from typing import Dict, List, Mapping, Optional, Sequence, Tuple


def parse_ansible_vault_header(first_line: str) -> Dict[str, Optional[str]]:
    """Parse the first line of an Ansible Vault file or inline block:
      `$ANSIBLE_VAULT;1.1;AES256` or `$ANSIBLE_VAULT;1.2;AES256;prod`
    Raises ValueError if the file is not encrypted with Ansible Vault.
    """
    line = first_line.strip()
    if not line.startswith("$ANSIBLE_VAULT;"):
        raise ValueError("NOT ENCRYPTED: missing $ANSIBLE_VAULT; header")
    parts = line.split(";")
    if len(parts) not in (3, 4) or parts[2] != "AES256":
        raise ValueError(f"invalid Ansible Vault header: {line!r}")
    return {
        "format_version": parts[1],
        "cipher": parts[2],
        "vault_id": parts[3] if len(parts) == 4 else None,
    }


def can_decrypt_vault_blob(
    first_line: str,
    supplied_vault_ids: Mapping[str, str],
    expected_label: str,
    expected_secret_key: str,
) -> bool:
    """Model Section 2 Vault ID environment isolation: a user holding only `dev`
    credentials in `supplied_vault_ids` cannot decrypt a `prod`-labeled vault file.
    """
    hdr = parse_ansible_vault_header(first_line)
    label = hdr["vault_id"] or "default"
    if label != expected_label:
        return False
    return supplied_vault_ids.get(label) == expected_secret_key


class TwoPhaseSecretRotator:
    """Model Section 7 zero-downtime two-phase credential rotation:
    1. Phase 1 (Expand): add new credential alongside old on provider (`active_keys = {old, new}`).
    2. Phase 2 (Roll consumers): update consumers to use `new`.
    3. Phase 3 (Contract): revoke `old` from provider only after all consumers use `new`.
    """

    def __init__(self, initial_key: str, consumers: Sequence[str]) -> None:
        self.provider_valid_keys = {initial_key}
        self.consumer_key: Dict[str, str] = {c: initial_key for c in consumers}

    def add_new_provider_key(self, new_key: str) -> None:
        self.provider_valid_keys.add(new_key)

    def update_consumer(self, consumer: str, new_key: str) -> bool:
        if new_key not in self.provider_valid_keys:
            raise PermissionError(f"consumer {consumer} rejected: key {new_key!r} not valid on provider")
        self.consumer_key[consumer] = new_key
        return True

    def revoke_old_provider_key(self, old_key: str) -> bool:
        still_using = [c for c, k in self.consumer_key.items() if k == old_key]
        if still_using:
            raise RuntimeError(f"cannot revoke {old_key!r}: still in use by {still_using}")
        self.provider_valid_keys.discard(old_key)
        return True
