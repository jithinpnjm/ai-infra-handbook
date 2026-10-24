"""Derive torch.distributed settings from Slurm environment variables (one task per GPU, launched by srun).

Pure standard library so it can be unit-tested without Slurm or torch.
"""
import os
import re
import subprocess


def expand_hostlist(expr):
    """Expand 'gpu[01-03,07],cpu1' -> ['gpu01','gpu02','gpu03','gpu07','cpu1']. Supports one bracket group per item."""
    items, depth, cur = [], 0, ""
    for ch in expr:
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        if ch == "," and depth == 0:
            items.append(cur)
            cur = ""
        else:
            cur += ch
    if cur:
        items.append(cur)
    out = []
    for item in items:
        m = re.match(r"^(.*?)\[([^\]]+)\](.*)$", item)
        if not m:
            out.append(item)
            continue
        pre, body, post = m.groups()
        for part in body.split(","):
            if "-" in part:
                a, b = part.split("-")
                out += [f"{pre}{i:0{len(a)}d}{post}" for i in range(int(a), int(b) + 1)]
            else:
                out.append(f"{pre}{part}{post}")
    return out


def first_host(nodelist):
    """Prefer 'scontrol show hostnames' (handles every hostlist form); fall back to the local expander."""
    try:
        out = subprocess.run(["scontrol", "show", "hostnames", nodelist], capture_output=True, text=True, check=True)
        return out.stdout.split()[0]
    except (OSError, subprocess.CalledProcessError, IndexError):
        return expand_hostlist(nodelist)[0]


def dist_env(env=None, port_base=10000):
    """Return the variables torch.distributed's env:// rendezvous needs."""
    e = os.environ if env is None else env
    job = int(e.get("SLURM_JOB_ID", "0"))
    return {
        "RANK": e["SLURM_PROCID"],
        "LOCAL_RANK": e["SLURM_LOCALID"],
        "WORLD_SIZE": e["SLURM_NTASKS"],
        "MASTER_ADDR": e.get("MASTER_ADDR") or first_host(e["SLURM_JOB_NODELIST"]),
        "MASTER_PORT": e.get("MASTER_PORT") or str(port_base + job % 20000),
    }


if __name__ == "__main__":
    for k, v in dist_env().items():
        print(f"{k}={v}")
