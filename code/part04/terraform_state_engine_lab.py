#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.19: Terraform state in depth: backends, locking and drift."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terraform_state_engine import (
    RemoteStateBackend,
    migrate_resource_between_states_declaratively,
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
    # 1. Section 4: Distributed state locking and force-unlock verification
    backend = RemoteStateBackend(lineage="b2a4c5f0-1111", initial_serial=10, initial_resources={"aws_vpc.main": "vpc-123"})
    ok1, _ = backend.acquire_lock("ci-job-1", "lock-abc")
    ok2, err2 = backend.acquire_lock("ci-job-2", "lock-def")
    backend.force_unlock("lock-abc")
    ok3, _ = backend.acquire_lock("ci-job-2", "lock-def")
    backend.release_lock("lock-def")
    check(
        "State lock blocks concurrent writer with LockID error until released or force-unlocked",
        ok1 is True and ok2 is False and "LockID=lock-abc" in err2 and ok3 is True,
    )

    # 2. Section 1, 4 & 7: Lineage/serial state-push safeguard and stale saved-plan rejection
    bad_lineage, _ = backend.push_state("wrong-lineage", 11, {})
    bad_serial, _ = backend.push_state("b2a4c5f0-1111", 9, {})
    ok_apply, _ = backend.apply_saved_plan(plan_serial=10, changes={"aws_subnet.a": "subnet-1"})
    stale_apply, stale_msg = backend.apply_saved_plan(plan_serial=10, changes={"aws_subnet.b": "subnet-2"})
    check(
        "Backend rejects state push with wrong lineage or older serial, increments serial on apply (10->11), and rejects stale plan",
        bad_lineage is False
        and bad_serial is False
        and ok_apply is True
        and backend.serial == 11
        and stale_apply is False
        and "Saved plan is stale" in stale_msg,
    )

    # 3. Section 7: Zero-downtime cross-state split via `import` + `removed { lifecycle { destroy = false } }`
    state_a = RemoteStateBackend("lin-a", 5, {"aws_s3_bucket.checkpoints": "acme-ml-checkpoints-prod"})
    state_b = RemoteStateBackend("lin-b", 1, {})
    mig = migrate_resource_between_states_declaratively(state_a, state_b, "aws_s3_bucket.checkpoints", destroy_on_remove=False)
    check(
        "Cross-state migration moves aws_s3_bucket.checkpoints from state_a to state_b with zero cloud destruction",
        mig["cloud_object_destroyed"] is False
        and mig["in_source"] is False
        and mig["in_target"] is True
        and mig["cloud_id_in_target"] == "acme-ml-checkpoints-prod",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
