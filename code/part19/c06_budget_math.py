"""Worked arithmetic for chapter 19.6: error budgets, pool fractions and loop latency.

Every input is an assumption stated in the chapter. Nothing here is measured.
"""
import math

HOURS_PER_MONTH = 730          # 8760 hours divided by 12


def downtime_budget_minutes(availability, hours=HOURS_PER_MONTH):
    """Minutes of allowed downtime for an availability target."""
    return (1 - availability) * hours * 60


def gpus_allowed_failing(health_target, gpus):
    """Whole GPUs that may be unhealthy at once under a GPU-health target."""
    return math.floor((1 - health_target) * gpus + 1e-9)


def pool_fraction_lost(nodes_out, nodes, gpus_per_node=8):
    """Share of the pool's GPUs that leave service when whole nodes are cordoned."""
    return nodes_out * gpus_per_node / (nodes * gpus_per_node)


def worst_case_detection_seconds(collect_interval=30, scrape_interval=30, eval_interval=60):
    """Slowest path from a fault to a firing alert when the rule has no for: clause.

    The exporter refreshes at its collect interval, Prometheus scrapes at its own
    interval, and the rule is evaluated at the evaluation interval. In the worst case
    the three waits add up.
    """
    return collect_interval + scrape_interval + eval_interval


def worst_case_cordon_seconds(unhealthy_for=120, requeue_slack=1):
    """Time from the condition turning False to the cordon: the window plus the requeue."""
    return unhealthy_for + requeue_slack


if __name__ == "__main__":
    for target in (0.99, 0.999, 0.995):
        print(f"availability {target:.3%}: {downtime_budget_minutes(target):7.1f} minutes a month")
    for gpus in (32, 100):
        print(f"98% GPU health on {gpus} GPUs: {gpus_allowed_failing(0.98, gpus)} may be failing")
    print(f"one node of four is {pool_fraction_lost(1, 4):.0%} of the pool")
    print(f"worst-case detection {worst_case_detection_seconds()} s, "
          f"worst-case cordon after the condition {worst_case_cordon_seconds()} s")
