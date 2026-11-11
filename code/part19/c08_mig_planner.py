#!/usr/bin/env python3
"""MIG partition planner for Chapter 19.8 (capstone: MIG multi-tenancy).

Data: c08_mig_profiles.json, extracted from the NVIDIA MIG User Guide
(Supported MIG Profiles, page last updated 2026-11-04, fetched 2026-11-10).

Model (documented): a seven-slice GPU has 8 memory slices and 7 SM slices.
Each profile has a fixed list of legal start positions, measured in memory
slices. The guide prints those lists as `nvidia-smi mig -lgipp` output for the
A100-SXM4-40GB. This module reuses the same geometry for every GPU in the guide
whose profile fractions match (A100 80GB, H100, H200, B200, GB200, B300, GB300).
That reuse is an inference. Confirm it on a real node with `nvidia-smi mig -lgipp`.

Not modelled: GPUs with four or two slices (A30, RTX PRO, Thor). The guide shows
their placements only as figures, so the planner refuses them.

Run the demo:  python3 code/part19/c08_mig_planner.py
"""
from __future__ import annotations

import json
import pathlib
import re
from dataclasses import dataclass, field
from itertools import product

HERE = pathlib.Path(__file__).resolve().parent
PROFILE_FILE = HERE / "c08_mig_profiles.json"

SEVEN_SLICE_MEM = 8
SEVEN_SLICE_SM = 7

# (sm_slices, mem_slices) -> legal start positions in memory slices.
# Source: nvidia-smi mig -lgipp on A100-SXM4-40GB, as printed in the guide
# (stored in c08_mig_profiles.json under a100_40gb_lgipp).
GEOMETRY_NOTE = "placements copied from the A100-40GB -lgipp listing; reuse for other GPUs is an inference"


class PlannerError(ValueError):
    """Raised for unknown profiles, unsupported GPUs and impossible requests."""


def load_data(path: pathlib.Path = PROFILE_FILE) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _fraction(text: str, whole: int) -> int | None:
    text = text.strip()
    if text == "Full":
        return whole
    m = re.fullmatch(r"(\d+)/(\d+)", text)
    if not m:
        return None
    num, den = int(m.group(1)), int(m.group(2))
    if (num * whole) % den:
        return None
    return num * whole // den


@dataclass(frozen=True)
class Profile:
    name: str
    sm_slices: int
    mem_slices: int
    starts: tuple[int, ...]
    max_instances: int
    media_extensions: bool = False

    @property
    def mem_gb_label(self) -> int:
        """The number in the profile name (memory in GB as NVIDIA rounds it)."""
        return int(re.search(r"\.(\d+)gb", self.name).group(1))


def _geometry(data: dict) -> dict[tuple[int, int], tuple[int, ...]]:
    geom = {}
    for name, info in data["a100_40gb_lgipp"]["placements"].items():
        if name.endswith("+me"):
            continue
        sm = int(name[0])
        geom[(sm, info["size"])] = tuple(info["starts"])
    return geom


def product_labels(data: dict | None = None) -> list[str]:
    data = data or load_data()
    return [t["product"] for t in data["tables"]]


def profiles_for(product_label: str, data: dict | None = None) -> dict[str, Profile]:
    """Profiles for one GPU product, keyed by profile name such as 1g.10gb."""
    data = data or load_data()
    table = next((t for t in data["tables"] if t["product"] == product_label), None)
    if table is None:
        raise PlannerError(f"unknown GPU product {product_label!r}; known: {product_labels(data)}")
    geom = _geometry(data)
    out: dict[str, Profile] = {}
    for row in table["rows"]:
        sm = _fraction(row["sm_fraction"], SEVEN_SLICE_SM)
        mem = _fraction(row["memory_fraction"], SEVEN_SLICE_MEM)
        if sm is None or mem is None:
            raise PlannerError(
                f"{product_label} is not a seven-slice GPU in the guide's tables; "
                "the planner only models 7 SM slices and 8 memory slices"
            )
        name = row["profile"]
        media = name.endswith("+me")
        key = (sm, mem)
        if key not in geom:
            raise PlannerError(f"no documented placement for {name} on {product_label}")
        out[name] = Profile(name, sm, mem, geom[key], row["max_instances"], media)
    return out


# ---------------------------------------------------------------- one GPU


def _fits(profile: Profile, start: int, used_mem: int, sm_used: int) -> bool:
    mask = ((1 << profile.mem_slices) - 1) << start
    if mask >> SEVEN_SLICE_MEM:
        return False
    return not (used_mem & mask) and sm_used + profile.sm_slices <= SEVEN_SLICE_SM


def feasible(profiles: list[Profile]) -> list[tuple[Profile, int]] | None:
    """Exact check that these instances can coexist on one GPU.

    Returns one legal placement as (profile, start) pairs, or None. Depth-first
    search, largest profile first. At most seven instances, so it is cheap.
    """
    order = sorted(profiles, key=lambda p: (-p.mem_slices, -p.sm_slices, p.name))
    # at most max_instances of each profile on one GPU
    counts: dict[str, int] = {}
    for p in order:
        counts[p.name] = counts.get(p.name, 0) + 1
        if counts[p.name] > p.max_instances:
            return None
    if sum(p.sm_slices for p in order) > SEVEN_SLICE_SM:
        return None

    def dfs(i: int, used_mem: int, sm_used: int, acc: list):
        if i == len(order):
            return list(acc)
        p = order[i]
        for s in p.starts:
            if _fits(p, s, used_mem, sm_used):
                acc.append((p, s))
                res = dfs(i + 1, used_mem | (((1 << p.mem_slices) - 1) << s), sm_used + p.sm_slices, acc)
                if res is not None:
                    return res
                acc.pop()
        return None

    return dfs(0, 0, 0, [])


def creation_order(profiles: list[Profile]) -> list[str]:
    """Order for `nvidia-smi mig -cgi`. The guide says the 3g profile must come first.

    Largest first satisfies that. mig-parted also retries permutations itself.
    """
    return [p.name for p in sorted(profiles, key=lambda p: (-p.mem_slices, -p.sm_slices, p.name))]


@dataclass
class GpuLayout:
    index: int
    placed: list[tuple[Profile, int, str]] = field(default_factory=list)  # profile, start, tenant

    def profiles(self) -> list[Profile]:
        return [p for p, _, _ in self.placed]

    @property
    def used_mem_slices(self) -> int:
        return sum(p.mem_slices for p in self.profiles())

    @property
    def used_sm_slices(self) -> int:
        return sum(p.sm_slices for p in self.profiles())

    @property
    def free_mem_slices(self) -> int:
        return SEVEN_SLICE_MEM - self.used_mem_slices

    @property
    def free_sm_slices(self) -> int:
        return SEVEN_SLICE_SM - self.used_sm_slices


def can_add(layout: GpuLayout, profile: Profile) -> bool:
    return feasible(layout.profiles() + [profile]) is not None


def _repack(layout: GpuLayout, profile: Profile, tenant: str) -> None:
    """Add an instance and recompute legal starts for the whole GPU."""
    tenants = [t for _, _, t in layout.placed] + [tenant]
    profs = layout.profiles() + [profile]
    order = sorted(range(len(profs)), key=lambda i: (-profs[i].mem_slices, -profs[i].sm_slices, profs[i].name))
    ordered = [profs[i] for i in order]
    placement = feasible(ordered)
    assert placement is not None
    # feasible() sorts the same way, so placement lines up with `ordered`
    layout.placed = [(p, s, tenants[order[k]]) for k, (p, s) in enumerate(placement)]


def fillable_extra(layout: GpuLayout, smallest: Profile) -> int:
    """How many more of the smallest profile still fit."""
    n = 0
    profs = layout.profiles()
    while feasible(profs + [smallest] * (n + 1)) is not None:
        n += 1
    return n


def layout_stats(layout: GpuLayout, profiles: dict[str, Profile]) -> dict:
    base = [p for p in profiles.values() if p.sm_slices == 1 and p.mem_slices == 1 and not p.media_extensions]
    smallest = base[0] if base else min(profiles.values(), key=lambda p: (p.mem_slices, p.sm_slices))
    extra = fillable_extra(layout, smallest)
    free_mem = layout.free_mem_slices
    stranded = free_mem - extra * smallest.mem_slices
    # largest single profile that still fits
    best = 0
    for p in profiles.values():
        if can_add(layout, p):
            best = max(best, p.mem_slices)
    frag = 0.0 if free_mem == 0 else round(1 - best / free_mem, 3)
    return {
        "gpu": layout.index,
        "instances": len(layout.placed),
        "used_mem_slices": layout.used_mem_slices,
        "used_sm_slices": layout.used_sm_slices,
        "free_mem_slices": free_mem,
        "free_sm_slices": layout.free_sm_slices,
        "stranded_mem_slices": stranded,
        "largest_free_mem_slices": best,
        "fragmentation": frag,
    }


# ---------------------------------------------------------------- many GPUs


@dataclass
class Plan:
    product: str
    gpus: list[GpuLayout]
    unplaced: list[tuple[str, str, int]]  # tenant, profile, count not placed
    profiles: dict[str, Profile]

    def stats(self) -> list[dict]:
        return [layout_stats(g, self.profiles) for g in self.gpus]

    def placed_by_tenant(self) -> dict[str, dict[str, int]]:
        out: dict[str, dict[str, int]] = {}
        for g in self.gpus:
            for p, _, t in g.placed:
                out.setdefault(t, {}).setdefault(p.name, 0)
                out[t][p.name] += 1
        return out

    def gpu_layout_names(self) -> list[list[str]]:
        return [creation_order(g.profiles()) for g in self.gpus]


def plan(product_label: str, gpu_count: int, demand: list[tuple[str, str, int]], data: dict | None = None) -> Plan:
    """Pack tenant demand onto gpu_count GPUs.

    demand is a list of (tenant, profile name, instance count). Largest profiles
    go first (first-fit decreasing). A request that fits nowhere is reported in
    `unplaced`, never silently dropped.
    """
    if gpu_count < 0:
        raise PlannerError("gpu_count must not be negative")
    profiles = profiles_for(product_label, data)
    items: list[tuple[Profile, str]] = []
    for tenant, pname, count in demand:
        if pname not in profiles:
            raise PlannerError(f"{pname!r} is not a profile of {product_label}; valid: {sorted(profiles)}")
        if count < 0:
            raise PlannerError("instance count must not be negative")
        items += [(profiles[pname], tenant)] * count
    items.sort(key=lambda it: (-it[0].mem_slices, -it[0].sm_slices, it[1], it[0].name))
    gpus = [GpuLayout(i) for i in range(gpu_count)]
    missed: dict[tuple[str, str], int] = {}
    for prof, tenant in items:
        for g in gpus:
            if can_add(g, prof):
                _repack(g, prof, tenant)
                break
        else:
            missed[(tenant, prof.name)] = missed.get((tenant, prof.name), 0) + 1
    unplaced = [(t, p, n) for (t, p), n in sorted(missed.items())]
    return Plan(product_label, gpus, unplaced, profiles)


def min_gpus(product_label: str, demand: list[tuple[str, str, int]], limit: int = 64, data: dict | None = None) -> int:
    """Smallest GPU count that places all demand with this packer."""
    for n in range(0, limit + 1):
        if not plan(product_label, n, demand, data).unplaced:
            return n
    raise PlannerError(f"demand does not fit on {limit} GPUs")


# ---------------------------------------------------------------- live GPU (instances cannot move)


def place_into_fixed(existing: list[tuple[Profile, int]], profile: Profile) -> int | None:
    """Start position for a new instance next to instances that are already running.

    Running instances cannot move. This is the situation after days of churn,
    and it is where stranded slices come from. Returns None when no legal start
    is free, even if enough slices are free in total.
    """
    used_mem = 0
    sm_used = 0
    count = 0
    for p, s in existing:
        used_mem |= ((1 << p.mem_slices) - 1) << s
        sm_used += p.sm_slices
        count += p.name == profile.name
    if count >= profile.max_instances:
        return None
    for s in profile.starts:
        if _fits(profile, s, used_mem, sm_used):
            return s
    return None


def fixed_fragmentation(existing: list[tuple[Profile, int]], profiles: dict[str, Profile]) -> dict:
    """Free memory slices versus the largest profile that can still start somewhere."""
    used = sum(p.mem_slices for p, _ in existing)
    free = SEVEN_SLICE_MEM - used
    best = 0
    for prof in profiles.values():
        if place_into_fixed(existing, prof) is not None:
            best = max(best, prof.mem_slices)
    return {"free_mem_slices": free, "largest_placeable_mem_slices": best, "fragmentation": 0.0 if free == 0 else round(1 - best / free, 3)}


# ---------------------------------------------------------------- spare capacity and mig-parted output


def fill_remaining(base: Plan, profile_name: str, tenant: str = "spare") -> Plan:
    """Add as many instances of one profile as still fit on each GPU (headroom)."""
    prof = base.profiles[profile_name]
    for g in base.gpus:
        while can_add(g, prof):
            _repack(g, prof, tenant)
    return base


def mig_parted_yaml(p: Plan, config_name: str, indent: str = "", all_disabled: bool = True) -> str:
    """Render the plan as a mig-parted config (version v1).

    GPUs with the same layout are grouped under one devices list. A GPU with no
    instances gets mig-enabled: false. The all-disabled entry is what the NVIDIA
    examples carry next to custom entries, so a node can be returned to full GPUs.
    The text is stable so a test can compare it with the committed file.
    """
    groups: dict[tuple[tuple[str, int], ...], list[int]] = {}
    for g in p.gpus:
        counts: dict[str, int] = {}
        for pr in g.profiles():
            counts[pr.name] = counts.get(pr.name, 0) + 1
        key = tuple(sorted(counts.items(), key=lambda kv: (-p.profiles[kv[0]].mem_slices, kv[0])))
        groups.setdefault(key, []).append(g.index)
    lines = ["version: v1", "mig-configs:"]
    if all_disabled:
        lines += ["  all-disabled:", "    - devices: all", "      mig-enabled: false", ""]
    lines += [f"  {config_name}:"]
    for key, idx in sorted(groups.items(), key=lambda kv: kv[1][0]):
        devs = ",".join(str(i) for i in idx)
        if not key:
            lines += [f"    - devices: [{devs}]", "      mig-enabled: false"]
            continue
        lines += [f"    - devices: [{devs}]", "      mig-enabled: true", "      mig-devices:"]
        lines += [f'        "{name}": {n}' for name, n in key]
    return "\n".join(indent + ln if ln else ln for ln in lines) + "\n"


# ---------------------------------------------------------------- figure cross-check


def figure_multisets(data: dict | None = None) -> set[tuple[int, ...]]:
    data = data or load_data()
    out = set()
    for cfg in data["seven_slice_valid_configs_figure"]["configs"]:
        out.add(tuple(sorted((x for x in cfg if x), reverse=True)))
    return out


def maximal_multisets(product_label: str = "H100 80GB (PCIe and SXM5)", data: dict | None = None) -> set[tuple[int, ...]]:
    """Maximal feasible mixes of the profiles the figure draws (no +me, no 1g.20gb)."""
    profs = profiles_for(product_label, data)
    drawn = [p for p in profs.values() if not p.media_extensions and not (p.sm_slices == 1 and p.mem_slices == 2)]
    by_sm = {p.sm_slices: p for p in drawn}
    sizes = sorted(by_sm)
    found = set()
    ranges = [range(0, SEVEN_SLICE_SM // s + 1) for s in sizes]
    feas = {}
    for combo in product(*ranges):
        plist = []
        for s, n in zip(sizes, combo):
            plist += [by_sm[s]] * n
        if plist and feasible(plist) is not None:
            feas[combo] = plist
    for combo, plist in feas.items():
        if all(feasible(plist + [by_sm[s]]) is None for s in sizes):
            found.add(tuple(sorted(sum(([s] * n for s, n in zip(sizes, combo)), []), reverse=True)))
    return found


# ---------------------------------------------------------------- demo


def _demo() -> None:
    prod = "H100 80GB (PCIe and SXM5)"
    demand = [
        ("search-embeddings", "1g.10gb", 10),
        ("chat-llm", "3g.40gb", 4),
        ("notebooks", "2g.20gb", 6),
        ("finetune", "4g.40gb", 2),
        ("batch-eval", "7g.80gb", 1),
    ]
    n = min_gpus(prod, demand)
    p = plan(prod, n, demand)
    print(f"{prod}: demand needs {n} GPUs with first-fit decreasing")
    for g, s in zip(p.gpu_layout_names(), p.stats()):
        print(f"  GPU {s['gpu']}: {g}  stranded_mem_slices={s['stranded_mem_slices']} frag={s['fragmentation']}")
    short = plan(prod, n - 1, demand)
    print("with one fewer GPU, unplaced:", short.unplaced)


if __name__ == "__main__":
    _demo()
