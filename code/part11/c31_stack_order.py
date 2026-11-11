"""Install-order checker for an AICR-shaped recipe (chapter 11.31).

AICR recipes list componentRefs, and each ref can name dependencyRefs. This module
reads that shape, rejects a missing dependency or a cycle, and returns one valid
install order. It also checks a short list of "must come after" rules taken from
upstream prerequisites. It is a handbook model, not the aicr engine.
"""
import heapq
from pathlib import Path

import yaml

# Prerequisites seen in upstream files (2026-11-11): the dynamo-platform, kai-scheduler
# and runai-cluster overlays in NVIDIA/aicr, and the NVSentinel README prerequisites.
REQUIRED_PRIORS = {
    "nvsentinel": ["gpu-operator", "cert-manager"],
    "kai-scheduler": ["gpu-operator"],
    "dynamo-platform": ["grove", "gpu-operator", "cert-manager", "kai-scheduler"],
    "runai-cluster": ["gpu-operator", "cert-manager", "prometheus-operator-crds"],
}


class RecipeError(ValueError):
    pass


def load_components(path):
    doc = yaml.safe_load(Path(path).read_text())
    refs = doc["spec"]["componentRefs"]
    graph = {}
    for ref in refs:
        name = ref["name"]
        if name in graph:
            raise RecipeError(f"duplicate component {name}")
        graph[name] = list(ref.get("dependencyRefs", []))
    return graph


def install_order(graph):
    for name, deps in graph.items():
        for dep in deps:
            if dep not in graph:
                raise RecipeError(f"{name} depends on {dep}, which is not in the recipe")
    waiting = {n: len(set(d)) for n, d in graph.items()}
    users = {n: [] for n in graph}
    for name, deps in graph.items():
        for dep in set(deps):
            users[dep].append(name)
    ready = [n for n, c in waiting.items() if c == 0]
    heapq.heapify(ready)
    order = []
    while ready:
        node = heapq.heappop(ready)
        order.append(node)
        for user in users[node]:
            waiting[user] -= 1
            if waiting[user] == 0:
                heapq.heappush(ready, user)
    if len(order) != len(graph):
        stuck = sorted(set(graph) - set(order))
        raise RecipeError("dependency cycle among " + ", ".join(stuck))
    return order


def rule_violations(graph):
    """Return messages for components that lack a required prior, directly or not."""
    problems = []
    for name, priors in REQUIRED_PRIORS.items():
        if name not in graph:
            continue
        reach = _reachable(graph, name)
        for prior in priors:
            if prior not in reach:
                problems.append(f"{name} must come after {prior}")
    return problems


def _reachable(graph, start):
    seen, stack = set(), list(graph[start])
    while stack:
        n = stack.pop()
        if n in seen or n not in graph:
            continue
        seen.add(n)
        stack.extend(graph[n])
    return seen
