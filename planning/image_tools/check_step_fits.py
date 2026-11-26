#!/usr/bin/env python3

# Let's check the widths and placements of each step if drawn on 1 line
steps_info = [
    # 1. U->>C: sbatch job.sh (RPC with munge credential)
    {"num": 1, "src": "U", "dst": "C", "type": "msg",
     "text": "sbatch job.sh (RPC with munge credential)",
     "mono_prefix": "sbatch job.sh", "sans_suffix": " (RPC with munge credential)",
     "x_start": 214},
     
    # 2. C->>C: authenticate, run job_submit plugin, check limits and associations
    {"num": 2, "src": "C", "dst": "C", "type": "self",
     "text": "authenticate, run job_submit plugin, check limits and associations",
     "x_start": 555},

    # 3. C-->>U: Submitted batch job 4217
    {"num": 3, "src": "C", "dst": "U", "type": "reply",
     "text": "Submitted batch job 4217",
     "x_start": 214},

    # 4. C->>C: job PENDING in queue, scheduler loop and backfill evaluate it
    {"num": 4, "src": "C", "dst": "C", "type": "self",
     "text": "job PENDING in queue, scheduler loop and backfill evaluate it",
     "x_start": 555},

    # 5. C->>C: resources found: allocate nodes A and B, state RUNNING
    {"num": 5, "src": "C", "dst": "C", "type": "self",
     "text": "resources found: allocate nodes A and B, state RUNNING",
     "x_start": 555, "orange": True},

    # 6. C->>D1: launch batch step (RPC tree fan-out)
    {"num": 6, "src": "C", "dst": "D1", "type": "msg",
     "text": "launch batch step (RPC tree fan-out)",
     "x_start": 524},

    # 7. C->>D2: prepare node (prolog)
    {"num": 7, "src": "C", "dst": "D2", "type": "msg",
     "text": "prepare node (prolog)",
     "x_start": 524},

    # 8. D1->>D1: prolog, fork slurmstepd, run the batch script
    {"num": 8, "src": "D1", "dst": "D1", "type": "self",
     "text": "prolog, fork slurmstepd, run the batch script",
     "x_start": 1175},

    # 9. D1->>D2: script runs srun, steps launched on both nodes
    {"num": 9, "src": "D1", "dst": "D2", "type": "msg",
     "text": "script runs srun, steps launched on both nodes",
     "x_start": 1144},

    # 10. D1->>D1: epilog, cleanup of processes
    {"num": 10, "src": "D1", "dst": "D1", "type": "self",
     "text": "epilog, cleanup of processes",
     "x_start": 1175},

    # 11. D2->>D2: epilog, cleanup of processes
    {"num": 11, "src": "D2", "dst": "D2", "type": "self",
     "text": "epilog, cleanup of processes",
     "x_start": 1450},

    # 12. D1->>C: job complete RPC
    {"num": 12, "src": "D1", "dst": "C", "type": "msg",
     "text": "job complete RPC",
     "x_start": 524},

    # 13. C->>DBD: job record: times, resources, exit code, usage
    {"num": 13, "src": "C", "dst": "DBD", "type": "msg",
     "text": "job record: times, resources, exit code, usage",
     "x_start": 524},

    # 14. C->>C: free nodes A and B, run scheduler again
    {"num": 14, "src": "C", "dst": "C", "type": "self",
     "text": "free nodes A and B, run scheduler again",
     "x_start": 555}
]

for s in steps_info:
    w = len(s["text"]) * 0.6 * 24
    xs = s["x_start"]
    xe = xs + w + 36
    print(f"Step {s['num']:2d} [{s['type']:5s}] xs={xs:4d} w={w:5.1f} xe={xe:6.1f} ({s['text'][:35]}...)")
