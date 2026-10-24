"""Mimic `srun --ntasks-per-node=T` on one machine: start N*T processes with the SLURM_* variables
a real srun would set, so launch glue can be tested without a cluster.
Usage: fake_srun.py NODES TASKS_PER_NODE command..."""
import os
import subprocess
import sys

nodes, per = int(sys.argv[1]), int(sys.argv[2])
cmd = sys.argv[3:]
nodelist = f"node[01-{nodes:02d}]" if nodes > 1 else "node01"
procs = []
for node in range(nodes):
    for local in range(per):
        env = dict(os.environ, SLURM_JOB_ID="4242", SLURM_JOB_NODELIST=nodelist, SLURM_NNODES=str(nodes),
                   SLURM_NTASKS=str(nodes * per), SLURM_NTASKS_PER_NODE=str(per),
                   SLURM_PROCID=str(node * per + local), SLURM_LOCALID=str(local), SLURM_NODEID=str(node),
                   MASTER_ADDR="127.0.0.1")           # real clusters resolve node01 via DNS; here everything is local
        procs.append(subprocess.Popen(cmd, env=env))
sys.exit(max(p.wait() for p in procs))
