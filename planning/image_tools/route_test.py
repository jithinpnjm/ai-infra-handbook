# Let's write a python solver/tester to find the cleanest, crossing-free layout.

# Nodes to place:
# Subgraph: users ("Login / submit nodes")
#   - U1: "sbatch, srun, salloc, squeue, sinfo, scancel"
#   - U2: "sacct, sacctmgr, sreport (accounting queries)"
#
# Subgraph: control ("Control plane")
#   - CTLD: "slurmctld\ncontroller, port 6817\nqueue, scheduler, node and job state"
#   - BACKUP: "backup slurmctld (optional)\nshared StateSaveLocation"
#   - DBD: "slurmdbd, port 6819\naccounting daemon"
#   - DB: "MariaDB / MySQL\naccounting database"
#   - REST: "slurmrestd (optional)\nREST API"
#
# Subgraph: compute ("Compute nodes (data plane)")
#   - D1: "slurmd, port 6818"
#   - D2: "slurmd"
#   - D3: "slurmd"
#   - STEPD: "slurmstepd\none per job step per node"
#   - JOB: "application processes"
#
# Standalone:
#   - MUNGE: "munge on every node\n(shared key, authenticates every request)"

# Total 15 connections:
# 1. U1 -> CTLD ("RPC + munge credential")
# 2. U2 -> DBD ("RPC")
# 3. CTLD <-> BACKUP
# 4. CTLD -> DBD ("job and usage records")
# 5. DBD -> DB
# 6. REST -> CTLD
# 7. CTLD -> D1 ("launch and control RPCs")
# 8. CTLD -> D2
# 9. CTLD -> D3
# 10. D1 -> STEPD
# 11. STEPD -> JOB ("runs your program")
# 12. U1 -> D1 ("srun talks to slurmd and slurmstepd directly")
# 13. MUNGE -.-> CTLD
# 14. MUNGE -.-> D1
# 15. MUNGE -.-> DBD

print("Analyzing planar layout...")
