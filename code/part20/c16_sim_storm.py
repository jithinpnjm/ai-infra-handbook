# code/part20/c16_sim_storm.py
"""Replay a burst of Xid 79 reports against the limiter and print what automation does."""
from c16_fleet_health import DrainLimiter, Fleet, Node

nodes = [Node(f"n{i:03d}", f"rack{i % 16}") for i in range(200)]
fleet = Fleet(nodes, DrainLimiter(200, max_fraction=0.05, trip_flags=6))
for second, name in enumerate(["n000", "n017", "n034", "n051", "n068", "n085", "n102"]):
    state = fleet.report_xid(name, second * 60, 79)
    print(f"t={second * 60:>3}s {name} -> {state.value:9} held={fleet.held.get(name, '-')}")
print("frozen:", fleet.limiter.frozen, "| serving:", fleet.serving(), "of", len(nodes))
