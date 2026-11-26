# docs/part-06-hpc-slurm/11-submitting-and-launching-jobs-sbatch-srun-salloc-arrays-dependencies.md
- ## Why this matters for AI infrastructure | 170 | NO FIGURE NEEDED introductory motivating text
- ## Prerequisites and outcomes | 130 | NO FIGURE NEEDED roadmap and prerequisites
- ## 1. Allocations, batch jobs and steps | 450 | COVERED(h11-batch-vs-steps, m6-11-1)
- ### The 6-stage Slurm job life cycle (*Supercomputers for Linux Sysadmins* Chapter 15) | 420 | NEEDS FIGURE 6-stage lifecycle across controller, node daemons, prolog/epilog, and cgroups
- ### Simulating a multi-node GPU cluster on a single physical machine (*Distributed AI Systems* Chapter 8) | 230 | COVERED(p3-0611-virtual-nodes)
- ## 2. A batch script | 530 | COVERED(p3-0611-batch-header-anatomy)
- ### Summary of primary `sbatch` / `srun` keys (*Supercomputers for Linux Sysadmins* Chapter 15 `Table 15-1`) | 200 | NO FIGURE NEEDED reference lookup table
- ### Rank-specific logging vs interleaved stdout (*Distributed AI Systems* Chapter 8) | 190 | COVERED(p3-0611-log-layers)
- ### Environment variables | 160 | COVERED(p3-0611-env-where-set)
- ### Distributed-training rendezvous from Slurm variables | 180 | COVERED(p3-0611-rendezvous-mapping)
- ## 3. srun | 360 | COVERED(p3-0611-srun-flags, p2-0611-step-inside-allocation)
- ### MPI and launching | 110 | NO FIGURE NEEDED brief text comparing srun with mpirun binding
- ## 4. Interactive jobs | 250 | COVERED(p3-0611-interactive-paths)
- ## 5. Job arrays | 320 | NEEDS FIGURE array master ID, task indices, throttle window, and config dispatch
- ### 2D hyperparameter grid search with job arrays (*Distributed AI Systems* Chapter 8) | 300 | COVERED(h11-array-grid)
- ## 6. Dependencies and pipelines | 380 | COVERED(p3-0611-dependency-types, h11-dependency-chain)
- ## 7. Time limits, signals, checkpoints, requeue | 510 | COVERED(p3-0611-checkpoint-layers, h11-signal-requeue)
- ## 8. Monitoring, modifying, cancelling | 480 | COVERED(p3-0611-query-tools)
- ## 9. A linter for batch scripts | 280 | COVERED(p3-0611-linter-findings)
- ## 10. Submission patterns for AI workloads | 230 | COVERED(p3-0611-submission-patterns)
- ## 11. Common mistakes | 310 | COVERED(p3-0611-mistake-table)
- ## 12. Lab (self-checking linter lab tested; cluster parts untested) | 360 | NO FIGURE NEEDED lab instructions
- ## 13. Interview angles | 140 | NO FIGURE NEEDED interview questions
- ## Exercises | 370 | NO FIGURE NEEDED exercises
- ## Checkpoint | 1150 | NO FIGURE NEEDED review Q&A
- ## Sources and review notes | 210 | NO FIGURE NEEDED sources and notes

Specs kept 2, dropped 0: []
