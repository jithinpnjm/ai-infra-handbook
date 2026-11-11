"""Switch and cable counts for a non-blocking (or oversubscribed) fat tree.

Standard Clos counting, checked in the tests against rows printed in
AI Data Center Network Design and Technologies ch. 3 and the DGX B200 and DGX GB300
SuperPOD documents. One endpoint = one NIC port on the compute fabric.
Two tiers: leaf and spine. Three tiers: leaf, spine and super spine, built from
pods that are 1:1 inside and may be oversubscribed at the super spine.
"""
import math


def _split(radix, oversub):
    if radix < 4 or radix % 2:
        raise ValueError("radix must be even and at least 4")
    if oversub < 1 or int(oversub) != oversub:
        raise ValueError("oversub must be a whole number >= 1")
    oversub = int(oversub)
    if (radix * oversub) % (oversub + 1):
        raise ValueError("radix cannot be split at %d:1 into whole ports" % oversub)
    down = radix * oversub // (oversub + 1)
    return down, radix - down


def fat_tree(endpoints, radix, leaf_oversub=1, top_oversub=1):
    """Return counts. leaf_oversub applies to the two-tier case only; top_oversub to
    the super spine of a three-tier fabric."""
    if endpoints < 1:
        raise ValueError("endpoints must be positive")
    down, up = _split(radix, leaf_oversub)
    leaves = math.ceil(endpoints / down)
    if leaves <= radix:
        spines = math.ceil(leaves * up / radix)
        return {"tiers": 2, "leaf": leaves, "spine": spines, "super_spine": 0,
                "switches": leaves + spines, "endpoint_cables": endpoints,
                "leaf_spine_cables": leaves * up, "spine_super_cables": 0,
                "leaf_oversub": leaf_oversub, "top_oversub": 1}
    if leaf_oversub != 1:
        raise ValueError("three tiers are built 1:1 inside a pod; use top_oversub")
    half = radix // 2
    pod_endpoints = half * half
    pods = math.ceil(endpoints / pod_endpoints)
    if pods > radix:
        raise ValueError("needs more than three tiers at this radix")
    spines = pods * half
    uplinks = spines * half
    supers = math.ceil(uplinks / radix / top_oversub)
    return {"tiers": 3, "leaf": leaves, "spine": spines, "super_spine": supers,
            "switches": leaves + spines + supers, "endpoint_cables": endpoints,
            "leaf_spine_cables": leaves * half, "spine_super_cables": uplinks,
            "leaf_oversub": 1, "top_oversub": top_oversub}


def max_two_tier_endpoints(radix, leaf_oversub=1):
    down, _ = _split(radix, leaf_oversub)
    return down * radix


def nvlink_domains(gpus, domain_size):
    """How many scale-up domains the job spans; traffic between them uses the NICs."""
    if gpus < 1 or domain_size < 1:
        raise ValueError("gpus and domain_size must be positive")
    return math.ceil(gpus / domain_size)


def scale_up_to_out_ratio(nvlink_gbytes_s, nic_gbit_s):
    """NVLink bytes per second per GPU over NIC bytes per second per GPU."""
    if nvlink_gbytes_s <= 0 or nic_gbit_s <= 0:
        raise ValueError("bandwidths must be positive")
    return nvlink_gbytes_s / (nic_gbit_s / 8.0)
