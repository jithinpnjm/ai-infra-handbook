"""Chapter 4.19 model: Terraform state `lineage` & `serial` optimistic
concurrency / stale-plan guard, distributed backend lock manager (`LockID`),
and zero-downtime cross-state resource migration (`import` + `removed`).

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR), Chapter 3 ("How to Manage Terraform State"):
  * Why `terraform.tfstate` must never be stored in Git (manual pull/push
    errors, lack of locking, plaintext secrets).
  * Bootstrapping the S3 backend (`aws_s3_bucket`, `aws_s3_bucket_versioning`,
    `aws_s3_bucket_server_side_encryption_configuration` `AES256`,
    `aws_s3_bucket_public_access_block`, and `aws_dynamodb_table` with
    `billing_mode = "PAY_PER_REQUEST"` and `hash_key = "LockID"` vs modern
    `use_lockfile = true`).
  * Partial backend configuration (`backend.hcl` + `terraform init
    -backend-config=backend.hcl`).
  * Isolating state via Workspaces (`env:/<workspace>/<key>`, `terraform.workspace`)
    vs File Layout (`stage`/`prod`/`mgmt`/`global` -> `vpc`/`services`/`data-stores`,
    with `main.tf`, `variables.tf`, `outputs.tf`, `dependencies.tf`, `providers.tf`).
  * `data "terraform_remote_state" "db"` and `templatefile("user-data.sh", ...)`.
- volume-10/05-terraform-for-infrastructure-as-code.md.
"""
from typing import Any, Dict, Optional, Tuple


class RemoteStateBackend:
    """Model a remote Terraform state backend with `lineage`, monotonically
    increasing `serial`, distributed lock (`LockID`), and stale-plan rejection.
    """

    def __init__(self, lineage: str, initial_serial: int = 1, initial_resources: Dict[str, str] | None = None) -> None:
        self.lineage = lineage
        self.serial = initial_serial
        self.resources: Dict[str, str] = dict(initial_resources or {})
        self.lock_id: Optional[str] = None
        self.lock_holder: Optional[str] = None

    def acquire_lock(self, holder: str, lock_id: str) -> Tuple[bool, str]:
        if self.lock_id is not None:
            return False, f"Error acquiring the state lock: LockID={self.lock_id} held by {self.lock_holder}"
        self.lock_id = lock_id
        self.lock_holder = holder
        return True, lock_id

    def release_lock(self, lock_id: str) -> None:
        if self.lock_id != lock_id:
            raise RuntimeError(f"cannot release lock: expected {self.lock_id}, got {lock_id}")
        self.lock_id = None
        self.lock_holder = None

    def force_unlock(self, lock_id: str) -> bool:
        if self.lock_id != lock_id:
            raise ValueError(f"LockID mismatch: expected {self.lock_id}, got {lock_id}")
        self.lock_id = None
        self.lock_holder = None
        return True

    def push_state(
        self,
        new_lineage: str,
        new_serial: int,
        new_resources: Dict[str, str],
        force: bool = False,
    ) -> Tuple[bool, str]:
        """Model `terraform state push` safety checks on `lineage` and `serial`."""
        if not force:
            if new_lineage != self.lineage:
                return False, f"refused: lineage {new_lineage!r} != backend lineage {self.lineage!r}"
            if new_serial <= self.serial:
                return False, f"refused: serial {new_serial} <= backend serial {self.serial}"
        self.lineage = new_lineage
        self.serial = new_serial
        self.resources = dict(new_resources)
        return True, "pushed"

    def apply_saved_plan(self, plan_serial: int, changes: Dict[str, str]) -> Tuple[bool, str]:
        """Model `terraform apply tfplan` rejecting a stale plan if `serial` advanced."""
        if plan_serial != self.serial:
            return False, f"Saved plan is stale: plan serial {plan_serial} != current state serial {self.serial}"
        self.resources.update(changes)
        self.serial += 1
        return True, f"applied (new serial={self.serial})"


def migrate_resource_between_states_declaratively(
    source_state: RemoteStateBackend,
    target_state: RemoteStateBackend,
    resource_addr: str,
    destroy_on_remove: bool = False,
) -> Dict[str, object]:
    """Model Section 7 zero-downtime cross-state split using `import {}` in
    `target_state` and `removed { lifecycle { destroy = false } }` in `source_state`.
    """
    if resource_addr not in source_state.resources:
        raise KeyError(f"{resource_addr} not found in source state")
    real_cloud_id = source_state.resources[resource_addr]

    # Step 1: target_state imports the existing cloud object ID
    target_state.resources[resource_addr] = real_cloud_id
    target_state.serial += 1

    # Step 2: source_state removes it from state without destroying the cloud object
    del source_state.resources[resource_addr]
    source_state.serial += 1

    return {
        "cloud_object_destroyed": destroy_on_remove,
        "in_source": resource_addr in source_state.resources,
        "in_target": resource_addr in target_state.resources,
        "cloud_id_in_target": target_state.resources.get(resource_addr),
    }
