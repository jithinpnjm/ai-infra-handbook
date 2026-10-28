#!/usr/bin/env python3
"""Slurm daemon port/role map, hierarchical RPC fan-out depth, and Munge credential validator for Chapter 6.7."""
import math

SLURM_DAEMON_PORTS = {
    "slurmctld": 6817,
    "slurmd": 6818,
    "slurmdbd": 6819,
    "vn1_virtual_slurmd": 17001,
    "vn2_virtual_slurmd": 17002,
}


def compute_rpc_tree_depth(num_nodes: int, tree_width: int = 50) -> dict[str, int]:
    """Compute RPC fan-out depth and first-hop messages for Slurm TreeWidth hierarchical launch."""
    if num_nodes <= 0:
        return {"depth": 0, "controller_direct_rpcs": 0}
    direct = min(num_nodes, tree_width)
    depth = 1 if num_nodes <= tree_width else int(math.ceil(math.log(num_nodes, tree_width)))
    return {
        "depth": depth,
        "controller_direct_rpcs": direct,
        "tree_width": tree_width,
    }


def validate_munge_credential(
    sender_key_hash: str,
    receiver_key_hash: str,
    sender_timestamp_s: float,
    receiver_timestamp_s: float,
    ttl_seconds: float = 300.0,
) -> dict[str, bool | str]:
    """Validate Munge shared secret key and clock skew window (default 300s / 5 minutes)."""
    if sender_key_hash != receiver_key_hash:
        return {"valid": False, "error": "Invalid credential (key mismatch)"}
    skew = receiver_timestamp_s - sender_timestamp_s
    if skew < -ttl_seconds:
        return {"valid": False, "error": "Rewound credential (future timestamp / clock skew)"}
    if skew > ttl_seconds:
        return {"valid": False, "error": "Expired credential (clock skew > TTL)"}
    return {"valid": True, "error": ""}


def check_test_partition_policy(max_time_minutes: int, max_queued_per_user: int) -> bool:
    """Verify SCL Chapter 13 dedicated test partition sizing rule (10-15 min max time, 3-5 queued tasks)."""
    return (10 <= max_time_minutes <= 15) and (3 <= max_queued_per_user <= 5)


if __name__ == "__main__":
    print("Slurm ports:", SLURM_DAEMON_PORTS)
    print("1024-node RPC tree (TreeWidth=50):", compute_rpc_tree_depth(1024, 50))
    print("Munge check (valid):", validate_munge_credential("k1", "k1", 1000.0, 1010.0))
    print("Test partition 15m / 4 tasks:", check_test_partition_policy(15, 4))
