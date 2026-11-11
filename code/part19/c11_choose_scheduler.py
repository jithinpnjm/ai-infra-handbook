"""Slurm versus Kubernetes decision rule with an explanation for every point.

The questions come from Supercomputers for Linux SysAdmins ch. 13 (Kubernetes is built
for scaling services, not topology, priorities or deep queues; HPC demand exceeds supply),
DGX GB300 RA (Mission Control offers Slurm and Kubernetes through Run:ai) and handbook
chapters 6.16, 11.13 to 11.20. The weights are MY judgement, not a measurement.
"""
REQUIRED = ("dedicated_training", "shared_with_services", "team_slurm_skill",
            "team_k8s_skill", "tenants", "demand_exceeds_supply",
            "needs_borrow_reclaim", "needs_gpu_fractions")


def choose_scheduler(p):
    missing = [k for k in REQUIRED if k not in p]
    if missing:
        raise ValueError("missing answers: " + ", ".join(missing))
    if p["tenants"] < 1:
        raise ValueError("tenants must be at least 1")
    s, k, why = 0, 0, []

    def add(side, pts, text):
        nonlocal s, k
        if side == "slurm":
            s += pts
        else:
            k += pts
        why.append("%s +%d: %s" % (side, pts, text))

    if p["dedicated_training"] and not p["shared_with_services"]:
        add("slurm", 2, "the estate runs batch training only")
    if p["shared_with_services"]:
        add("k8s", 2, "inference, notebooks or services share the GPUs")
    if p["team_slurm_skill"]:
        add("slurm", 1, "the team already operates Slurm")
    if p["team_k8s_skill"]:
        add("k8s", 1, "the team already operates Kubernetes")
    if p["demand_exceeds_supply"]:
        add("slurm", 1, "queues are deep, and Slurm queues, priorities and backfills natively")
    if p["tenants"] >= 5 or p["needs_borrow_reclaim"]:
        add("k8s", 1, "many tenants or borrow-and-reclaim quotas map to Kueue or KAI queues")
    if abs(s - k) <= 1 and min(s, k) >= 2:
        pick = "Slurm on Kubernetes (Slinky or Soperator)"
        why.append("scores are close and both sides are strong: run Slurm on a Kubernetes substrate")
    elif s > k:
        pick = "Slurm"
    elif k > s:
        pick = "Kubernetes with " + ("KAI" if p["needs_gpu_fractions"] else "Kueue")
    else:
        pick = "undecided: tie with weak evidence, run a two-week pilot"
        why.append("tie")
    if pick.startswith("Kubernetes"):
        why.append("KAI chosen for GPU fractions" if p["needs_gpu_fractions"]
                   else "Kueue chosen: quota admission is enough without GPU fractions")
    return {"choice": pick, "slurm_score": s, "k8s_score": k, "reasons": why}
