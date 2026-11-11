"""Failure-domain blast radius and spare capacity for chapter 20.34.

A fleet is a tree: site, hall, row, rack, node. A fault takes out one
domain at one level. This model answers three questions for a layout
you state yourself: how many nodes does a fault remove, how many serving
replicas survive the worst single fault, and how many spare replicas
you must hold to keep a required number alive. Standard library only.

Nothing here describes a real Nebius site. Nebius has not published its
hall, row or rack counts. Every number comes from the caller.
"""
import math
from dataclasses import dataclass

LEVELS = ("node", "rack", "row", "hall", "site")


@dataclass(frozen=True)
class Layout:
    sites: int = 1
    halls_per_site: int = 2
    rows_per_hall: int = 4
    racks_per_row: int = 6
    nodes_per_rack: int = 8
    gpus_per_node: int = 8

    def __post_init__(self):
        for name in ("sites", "halls_per_site", "rows_per_hall",
                     "racks_per_row", "nodes_per_rack", "gpus_per_node"):
            if getattr(self, name) < 1:
                raise ValueError(f"{name} must be at least 1")

    @property
    def racks(self):
        return (self.sites * self.halls_per_site
                * self.rows_per_hall * self.racks_per_row)

    @property
    def total_nodes(self):
        return self.racks * self.nodes_per_rack

    @property
    def total_gpus(self):
        return self.total_nodes * self.gpus_per_node

    def nodes_per_domain(self, level):
        """How many nodes one domain at this level contains."""
        per = {
            "node": 1,
            "rack": self.nodes_per_rack,
            "row": self.nodes_per_rack * self.racks_per_row,
            "hall": (self.nodes_per_rack * self.racks_per_row
                     * self.rows_per_hall),
            "site": (self.nodes_per_rack * self.racks_per_row
                     * self.rows_per_hall * self.halls_per_site),
        }
        if level not in per:
            raise ValueError(f"unknown level {level!r}")
        return per[level]

    def domain_count(self, level):
        return self.total_nodes // self.nodes_per_domain(level)

    def domain_of(self, node, level):
        """Index of the domain at `level` that holds node number `node`."""
        if not 0 <= node < self.total_nodes:
            raise ValueError("node out of range")
        return node // self.nodes_per_domain(level)

    def nodes_in(self, level, domain_id):
        size = self.nodes_per_domain(level)
        if not 0 <= domain_id < self.domain_count(level):
            raise ValueError("domain out of range")
        return list(range(domain_id * size, (domain_id + 1) * size))


@dataclass(frozen=True)
class Blast:
    nodes: int
    gpus: int
    fraction: float


def blast_radius(layout, level):
    """What one fault at `level` removes from the fleet."""
    nodes = layout.nodes_per_domain(level)
    return Blast(nodes, nodes * layout.gpus_per_node,
                 nodes / layout.total_nodes)


# Power wiring models from the DGX B200 data centre design book. A B200
# node has six power supplies and needs five energised. The book calls
# the all-on-one-feed model the non-interleaved one. It is described
# there as half-rack loss when one feed fails. Interleaving three cords
# per feed leaves 3 of 6 supplies and crashes every node. Six discrete
# sources leave 5 of 6 on any single feed loss.
POWER_MODELS = ("interleaved_two_feed", "non_interleaved_two_feed",
                "six_discrete_sources")


def nodes_lost_on_single_feed_failure(model, nodes_in_rack):
    """Nodes in one rack that stop when one power feed fails."""
    if model == "interleaved_two_feed":
        return nodes_in_rack
    if model == "non_interleaved_two_feed":
        return math.ceil(nodes_in_rack / 2)
    if model == "six_discrete_sources":
        return 0
    raise ValueError(f"unknown power model {model!r}")


def psu_node_survives(psus_up, psus_needed=5):
    """A node runs only while enough power supplies are energised."""
    return psus_up >= psus_needed


def rail_bandwidth_fraction(nics_per_node, nics_down):
    """Share of scale-out bandwidth a node keeps after losing NICs.

    A leaf failure in a rail-optimised fabric removes one rail's link
    from every node attached to that leaf. The node stays up. Whether
    the job tolerates the lower bandwidth is a job question.
    """
    if not 0 <= nics_down <= nics_per_node:
        raise ValueError("nics_down out of range")
    return (nics_per_node - nics_down) / nics_per_node


def _interleaved_racks(layout):
    """Rack numbers ordered so neighbours in the list sit in different
    sites, then halls, then rows. Dealing replicas along this list
    spreads them across the largest domains first.
    """
    def key(rack):
        rack, in_row = divmod(rack, layout.racks_per_row)
        rack, row = divmod(rack, layout.rows_per_hall)
        site, hall = divmod(rack, layout.halls_per_site)
        return (in_row, row, hall, site)
    return sorted(range(layout.racks), key=key)


def _place(layout, replicas, nodes_per_replica, policy):
    """Return a list of replicas, each a tuple of node numbers.

    A replica must sit inside one rack, as a rack-scale NVLink domain
    requires. `pack` fills racks in order. `spread` deals replicas out
    to racks in turn. Returns None if the layout cannot hold them.
    """
    if nodes_per_replica < 1:
        raise ValueError("nodes_per_replica must be at least 1")
    per_rack = layout.nodes_per_rack // nodes_per_replica
    if per_rack < 1 or replicas > per_rack * layout.racks:
        return None
    placed = []
    if policy == "pack":
        for r in range(replicas):
            rack, slot = divmod(r, per_rack)
            base = rack * layout.nodes_per_rack + slot * nodes_per_replica
            placed.append(tuple(range(base, base + nodes_per_replica)))
    elif policy == "spread":
        order = _interleaved_racks(layout)
        used = [0] * layout.racks
        for r in range(replicas):
            rack = order[r % layout.racks]
            base = (rack * layout.nodes_per_rack
                    + used[rack] * nodes_per_replica)
            used[rack] += 1
            placed.append(tuple(range(base, base + nodes_per_replica)))
    else:
        raise ValueError("policy must be pack or spread")
    return placed


def surviving_replicas(layout, replicas, nodes_per_replica, level, policy):
    """Replicas left after the worst single fault at `level`.

    The worst fault is the domain holding the most replicas. A replica
    dies if any of its nodes is in the failed domain. Returns None if
    the placement does not fit.
    """
    placed = _place(layout, replicas, nodes_per_replica, policy)
    if placed is None:
        return None
    lost_by_domain = {}
    for nodes in placed:
        for d in {layout.domain_of(n, level) for n in nodes}:
            lost_by_domain[d] = lost_by_domain.get(d, 0) + 1
    worst = max(lost_by_domain.values()) if lost_by_domain else 0
    return replicas - worst


def spares_needed(layout, required, nodes_per_replica, level, policy):
    """Extra replicas to keep `required` alive after the worst fault.

    Returns the number of spares, or None if no count fits the layout.
    """
    total = required
    while True:
        alive = surviving_replicas(layout, total, nodes_per_replica,
                                   level, policy)
        if alive is None:
            return None
        if alive >= required:
            return total - required
        total += 1


def plan_drain(layout, level, domain_id, max_out_fraction,
               already_out=0, load=None):
    """Split a planned drain of one domain into safe batches.

    No batch may push nodes-out above `max_out_fraction` of the fleet,
    counting nodes already out. Within the domain the least loaded
    nodes go first. Returns a list of batches, or None if the budget
    leaves no room for even one node.
    """
    budget = math.floor(layout.total_nodes * max_out_fraction) - already_out
    if budget < 1:
        return None
    nodes = layout.nodes_in(level, domain_id)
    load = load or {}
    nodes.sort(key=lambda n: (load.get(n, 0), n))
    return [nodes[i:i + budget] for i in range(0, len(nodes), budget)]


if __name__ == "__main__":
    lay = Layout(sites=1, halls_per_site=2, rows_per_hall=4,
                 racks_per_row=6, nodes_per_rack=8)
    print(f"{lay.total_nodes} nodes, {lay.total_gpus} GPUs")
    for lvl in LEVELS[:-1]:
        b = blast_radius(lay, lvl)
        print(f"{lvl:5s} fault removes {b.nodes:3d} nodes "
              f"({b.fraction:.1%} of fleet)")
    for pol in ("pack", "spread"):
        for lvl in ("rack", "row", "hall"):
            sp = spares_needed(lay, 40, 1, lvl, pol)
            print(f"policy={pol:6s} level={lvl:4s} spares for 40 nodes: {sp}")
