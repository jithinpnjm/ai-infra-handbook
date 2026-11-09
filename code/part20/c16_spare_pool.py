# code/part20/c16_spare_pool.py
"""Spare pool sizing from a failure rate and a repair time (chapter 20.16).

Inputs are assumptions you pass in. Nothing here is a measured fleet figure.
"""
import math


def expected_in_repair(fleet_nodes, annual_failure_rate, mttr_hours):
    """Little's law: arrivals per hour times hours each node stays out."""
    return fleet_nodes * annual_failure_rate / 8760.0 * mttr_hours


def poisson_cdf(k, mean):
    term = total = math.exp(-mean)
    for i in range(1, k + 1):
        term *= mean / i
        total += term
    return total


def spares_needed(fleet_nodes, annual_failure_rate, mttr_hours, coverage=0.999):
    """Smallest s with P(nodes in repair <= s) >= coverage, Poisson model."""
    mean = expected_in_repair(fleet_nodes, annual_failure_rate, mttr_hours)
    s = 0
    while poisson_cdf(s, mean) < coverage:
        s += 1
    return s


def x_plus_k(required_replicas, nodes_per_replica, spares):
    """Node count to buy for a customer promise of required_replicas."""
    return required_replicas * nodes_per_replica + spares


def effective_capacity(total_nodes, in_repair, stuck, in_maintenance=0):
    """Serving nodes. Stuck nodes are in repair on paper and lost in practice."""
    return total_nodes - in_repair - stuck - in_maintenance


if __name__ == "__main__":
    for mttr in (24, 72, 336):
        mean = expected_in_repair(512, 0.10, mttr)
        print(f"MTTR {mttr:>3} h  mean in repair {mean:5.2f}  "
              f"spares for 99.9%: {spares_needed(512, 0.10, mttr)}")
