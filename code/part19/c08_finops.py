#!/usr/bin/env python3
"""Cost per MIG slice: chargeback maths, Prometheus rules and Grafana dashboard (Chapter 19.8).

Everything priced here uses an ILLUSTRATIVE GPU-hour price passed in by the caller.
The default is a placeholder, not a quote from any cloud or vendor.

Charging rule (my design choice, not an NVIDIA rule): a slice's share of a GPU is the
average of its memory share and its SM share,

    weight = (memory_slices / 8 + sm_slices / 7) / 2

Memory slices never overlap and SM slices never exceed 7, so the weights of the
instances on one GPU always add up to at most 1. The remainder is cost nobody can
use: it is reported as layout loss, not charged to a tenant.

Run:  python3 code/part19/c08_finops.py          (prints the worked example)
      python3 code/part19/c08_finops.py --write  (rewrites the rules file and dashboard JSON)
"""
from __future__ import annotations

import json
import pathlib
import sys
from fractions import Fraction

import c08_mig_planner as planner

HERE = pathlib.Path(__file__).resolve().parent
DASHBOARD_FILE = HERE / "c08_finops_mig_dashboard.json"
RULES_FILE = HERE / "c08_mig_rules.yml"

EXAMPLE_PRODUCT = "H100 80GB (PCIe and SXM5)"
EXAMPLE_PRICE_PER_GPU_HOUR = 4.00  # placeholder in USD, replace with your contract price
HOURS_PER_MONTH = 730  # 365 * 24 / 12, rounded

TENANT_MIX = [
    ("search-embeddings", "1g.10gb", 10),
    ("chat-llm", "3g.40gb", 4),
    ("notebooks", "2g.20gb", 6),
    ("finetune", "4g.40gb", 2),
    ("batch-eval", "7g.80gb", 1),
]


def blended_weight(profile: planner.Profile) -> Fraction:
    return (Fraction(profile.mem_slices, planner.SEVEN_SLICE_MEM) + Fraction(profile.sm_slices, planner.SEVEN_SLICE_SM)) / 2


def slice_price(profile: planner.Profile, price_per_gpu_hour: float) -> float:
    return float(blended_weight(profile)) * price_per_gpu_hour


def node_layout(product: str = EXAMPLE_PRODUCT, demand=None, gpus: int = 8, spare_profile: str = "1g.10gb") -> planner.Plan:
    """The tenant-mix node used throughout the chapter: planned, then filled with spare slices."""
    p = planner.plan(product, gpus, demand or TENANT_MIX)
    if p.unplaced:
        raise planner.PlannerError(f"demand does not fit on {gpus} GPUs: {p.unplaced}")
    planner.fill_remaining(p, spare_profile)
    return p


def chargeback(layout: planner.Plan, reserved: dict[str, dict[str, int]], price_per_gpu_hour: float, hours: float = HOURS_PER_MONTH) -> dict:
    """Split the cost of the GPUs in `layout` over tenants.

    reserved maps tenant -> {profile: instance count held for the period}. A tenant
    cannot reserve more instances of a profile than the layout offers.
    Returns cost per tenant plus two kinds of cost no tenant pays:
      idle: slices that exist but nobody reserved
      layout_loss: GPU share that no profile in the layout can use
    The four parts always add up to the full cost of the GPUs.
    """
    if price_per_gpu_hour < 0 or hours < 0:
        raise ValueError("price and hours must not be negative")
    offered: dict[str, int] = {}
    for g in layout.gpus:
        for pr in g.profiles():
            offered[pr.name] = offered.get(pr.name, 0) + 1
    for tenant, held in reserved.items():
        for name, n in held.items():
            if name not in offered:
                raise ValueError(f"{tenant} reserves {name}, which the layout does not offer")
            if n < 0:
                raise ValueError("reserved counts must not be negative")
    totals = {name: sum(h.get(name, 0) for h in reserved.values()) for name in offered}
    for name, n in totals.items():
        if n > offered[name]:
            raise ValueError(f"{name}: {n} reserved but only {offered[name]} offered")

    gpu_cost = price_per_gpu_hour * hours * len(layout.gpus)
    per_tenant: dict[str, float] = {}
    sold = Fraction(0)
    for tenant, held in reserved.items():
        w = sum(blended_weight(layout.profiles[name]) * n for name, n in held.items())
        sold += w
        per_tenant[tenant] = float(w) * price_per_gpu_hour * hours
    offered_weight = sum(blended_weight(layout.profiles[name]) * n for name, n in offered.items())
    idle_weight = offered_weight - sold
    loss_weight = len(layout.gpus) - offered_weight
    return {
        "gpu_cost": gpu_cost,
        "tenants": per_tenant,
        "idle": float(idle_weight) * price_per_gpu_hour * hours,
        "layout_loss": float(loss_weight) * price_per_gpu_hour * hours,
        "offered": offered,
    }


def fully_loaded(result: dict) -> dict[str, float]:
    """Spread idle cost over tenants in proportion to what they already pay. Layout loss stays with the platform."""
    paid = sum(result["tenants"].values())
    if paid == 0:
        return dict(result["tenants"])
    return {t: c + result["idle"] * c / paid for t, c in result["tenants"].items()}


def cost_per_busy_hour(allocated_cost: float, average_utilisation: float) -> float:
    """Cost of an hour of real work: allocated cost divided by the fraction of time the slice was busy."""
    if not 0 < average_utilisation <= 1:
        raise ValueError("average_utilisation must be in (0, 1]")
    return allocated_cost / average_utilisation


# ---------------------------------------------------------------- Prometheus rules and dashboard

KUEUE_RES = "nvidia.com/mig-{}"
KSM_RES = "nvidia_com_mig_{}"


def _prom_profile_key(name: str) -> str:
    return name.replace(".", "_").replace("+", "_")


def price_table(layout: planner.Plan, price_per_gpu_hour: float) -> dict[str, float]:
    """USD per slice-hour for every non +me profile the layout can create."""
    return {
        name: round(slice_price(pr, price_per_gpu_hour), 4)
        for name, pr in layout.profiles.items()
        if not pr.media_extensions
    }


def build_rules(prices: dict[str, float]) -> str:
    lines = [
        "# Prometheus rules for the MIG capstone (Chapter 19.8). Checked with: promtool check rules",
        "# Prices are ILLUSTRATIVE (see c08_finops.py). Replace them with your contract price.",
        "groups:",
        "  - name: c08-mig-price",
        "    rules:",
    ]
    for name in sorted(prices, key=lambda n: (int(n[0]), n)):
        res = KUEUE_RES.format(name)
        lines += [
            "      - record: c08:mig_slice_price_per_hour",
            f"        expr: vector({prices[name]})",
            "        labels:",
            f"          resource: \"{res}\"",
        ]
    lines += [
        "  - name: c08-mig-alerts",
        "    rules:",
        "      - alert: C08MigSliceReservedButIdle",
        "        expr: avg_over_time(DCGM_FI_PROF_GR_ENGINE_UTIL_RATIO{GPU_I_PROFILE!=\"\"}[6h]) < 0.05",
        "        for: 30m",
        "        labels:",
        "          severity: info",
        "        annotations:",
        "          summary: \"MIG instance {{ $labels.GPU_I_PROFILE }} on GPU {{ $labels.gpu }} has been almost idle for 6 hours\"",
        "      - alert: C08MigInstanceMemoryNearFull",
        "        expr: DCGM_FI_DEV_FB_USED_BYTES{GPU_I_PROFILE!=\"\"} / (DCGM_FI_DEV_FB_USED_BYTES{GPU_I_PROFILE!=\"\"} + DCGM_FI_DEV_FB_FREE_BYTES{GPU_I_PROFILE!=\"\"}) > 0.9",
        "        for: 10m",
        "        labels:",
        "          severity: warning",
        "        annotations:",
        "          summary: \"MIG instance {{ $labels.GPU_I_PROFILE }} on GPU {{ $labels.gpu }} is above 90 percent of its memory\"",
        "      - alert: C08MigWorkloadsPendingWhileSlicesFree",
        "        expr: sum by (cluster_queue) (kueue_pending_workloads{status=\"active\"}) > 0 and on () (sum(kube_node_status_allocatable{resource=~\"nvidia_com_mig_.*\"}) - sum(kube_pod_container_resource_requests{resource=~\"nvidia_com_mig_.*\"})) > 0",
        "        for: 15m",
        "        labels:",
        "          severity: warning",
        "        annotations:",
        "          summary: \"Queue {{ $labels.cluster_queue }} has pending workloads while MIG slices of some profile are free: check profile mismatch and fragmentation\"",
    ]
    return "\n".join(lines) + "\n"


def build_dashboard(prices: dict[str, float]) -> dict:
    mig = 'resource=~"nvidia.com/mig-.*"'
    ksm_mig = 'resource=~"nvidia_com_mig_.*"'
    inst = 'GPU_I_PROFILE!=""'

    def panel(pid, title, ptype, expr, legend, x, y, w=12, h=8, unit=None, desc=""):
        fc = {"defaults": {}, "overrides": []}
        if unit:
            fc["defaults"]["unit"] = unit
        return {
            "id": pid,
            "title": title,
            "type": ptype,
            "description": desc,
            "gridPos": {"x": x, "y": y, "w": w, "h": h},
            "datasource": {"type": "prometheus", "uid": "${datasource}"},
            "fieldConfig": fc,
            "targets": [{"refId": "A", "expr": expr, "legendFormat": legend}],
        }

    panels = [
        panel(1, "Cost per tenant, USD per hour (reserved slices)", "bargauge",
              f'sum by (cluster_queue) (kueue_cluster_queue_resource_reservation{{{mig}}} * on (resource) group_left () c08:mig_slice_price_per_hour)',
              "{{cluster_queue}}", 0, 0, unit="currencyUSD",
              desc="Needs metrics.enableClusterQueueResources in the Kueue manager config. Price rules come from c08_mig_rules.yml."),
        panel(2, "Reserved slices per tenant and profile", "timeseries",
              f'sum by (cluster_queue, resource) (kueue_cluster_queue_resource_reservation{{{mig}}})',
              "{{cluster_queue}} {{resource}}", 12, 0),
        panel(3, "Nominal quota versus reservation per profile", "timeseries",
              f'sum by (resource) (kueue_cluster_queue_nominal_quota{{{mig}}}) - sum by (resource) (kueue_cluster_queue_resource_reservation{{{mig}}})',
              "{{resource}}", 0, 8,
              desc="Positive means quota that nobody holds. Compare with the free slices in the next panel."),
        panel(4, "Free slices per profile (allocatable minus requested)", "timeseries",
              f'sum by (resource) (kube_node_status_allocatable{{{ksm_mig}}}) - sum by (resource) (kube_pod_container_resource_requests{{{ksm_mig}}})',
              "{{resource}}", 12, 8,
              desc="kube-state-metrics sanitises resource names: nvidia.com/mig-1g.10gb appears as nvidia_com_mig_1g_10gb."),
        panel(5, "SM activity per MIG instance", "timeseries",
              f'avg by (gpu, GPU_I_ID, GPU_I_PROFILE) (DCGM_FI_PROF_GR_ENGINE_UTIL_RATIO{{{inst}}})',
              "gpu {{gpu}} gi {{GPU_I_ID}} {{GPU_I_PROFILE}}", 0, 16, unit="percentunit"),
        panel(6, "Memory used per MIG instance", "timeseries",
              f'DCGM_FI_DEV_FB_USED_BYTES{{{inst}}}',
              "gpu {{gpu}} gi {{GPU_I_ID}} {{GPU_I_PROFILE}}", 12, 16, unit="bytes"),
        panel(7, "Memory pressure per MIG instance", "timeseries",
              f'DCGM_FI_DEV_FB_USED_BYTES{{{inst}}} / (DCGM_FI_DEV_FB_USED_BYTES{{{inst}}} + DCGM_FI_DEV_FB_FREE_BYTES{{{inst}}})',
              "gpu {{gpu}} gi {{GPU_I_ID}} {{GPU_I_PROFILE}}", 0, 24, unit="percentunit"),
        panel(8, "Pending workloads per queue", "timeseries",
              'sum by (cluster_queue, status) (kueue_pending_workloads)',
              "{{cluster_queue}} {{status}}", 12, 24),
        panel(9, "Weighted share per queue (above 0 means borrowing)", "timeseries",
              'kueue_cluster_queue_weighted_share', "{{cluster_queue}}", 0, 32),
        panel(10, "Monthly cost of idle slices, USD", "stat",
              f'sum(((sum by (resource) (kueue_cluster_queue_nominal_quota{{{mig}}}) - sum by (resource) (kueue_cluster_queue_resource_reservation{{{mig}}})) * on (resource) group_left () c08:mig_slice_price_per_hour)) * {HOURS_PER_MONTH}',
              "idle", 12, 32, unit="currencyUSD",
              desc="Quota that exists but is not reserved, priced per slice."),
    ]
    return {
        "title": "AI Factory - MIG FinOps and per-instance health",
        "uid": "c08-mig-finops",
        "schemaVersion": 39,
        "version": 1,
        "editable": True,
        "tags": ["mig", "finops", "capstone"],
        "time": {"from": "now-24h", "to": "now"},
        "templating": {
            "list": [
                {"name": "datasource", "type": "datasource", "query": "prometheus", "label": "Data source"},
            ]
        },
        "panels": panels,
        "_comment": "Prices in c08_mig_rules.yml are illustrative. Panels were checked for PromQL syntax only; not run against live data.",
    }


def expressions(dashboard: dict) -> list[str]:
    return [t["expr"] for p in dashboard["panels"] for t in p["targets"]]


def render_files() -> tuple[str, str]:
    layout = node_layout()
    prices = price_table(layout, EXAMPLE_PRICE_PER_GPU_HOUR)
    return build_rules(prices), json.dumps(build_dashboard(prices), indent=2) + "\n"


def _demo() -> None:
    layout = node_layout()
    reserved = {t: {p: n} for t, p, n in TENANT_MIX}
    reserved["search-embeddings"] = {"1g.10gb": 10}
    res = chargeback(layout, reserved, EXAMPLE_PRICE_PER_GPU_HOUR)
    print(f"price {EXAMPLE_PRICE_PER_GPU_HOUR} USD per GPU-hour (illustrative), {HOURS_PER_MONTH} hours, 8 GPUs")
    print(f"node cost {res['gpu_cost']:.2f}")
    for t, c in res["tenants"].items():
        print(f"  {t:18s} {c:9.2f}")
    print(f"  idle slices        {res['idle']:9.2f}")
    print(f"  layout loss        {res['layout_loss']:9.2f}")
    for name, pr in sorted(layout.profiles.items(), key=lambda kv: (kv[1].sm_slices, kv[0])):
        if not pr.media_extensions:
            print(f"  slice {name:9s} weight {float(blended_weight(pr)):.4f}  {slice_price(pr, EXAMPLE_PRICE_PER_GPU_HOUR):.3f} USD/h")


if __name__ == "__main__":
    if "--write" in sys.argv:
        rules, dash = render_files()
        RULES_FILE.write_text(rules, encoding="utf-8")
        DASHBOARD_FILE.write_text(dash, encoding="utf-8")
        print("wrote", RULES_FILE.name, DASHBOARD_FILE.name)
    else:
        _demo()
