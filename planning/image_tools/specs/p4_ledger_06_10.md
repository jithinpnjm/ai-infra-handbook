# docs/part-06-hpc-slurm/10-slurm-gpu-scheduling-gres-nvml-autodetect-mig-and-device-constraints.md
- ## Why this matters for AI infrastructure | 160 | NO FIGURE NEEDED introductory context and motivation
- ## Prerequisites and outcomes | 165 | NO FIGURE NEEDED outline and prerequisites list
- ## 1. Generic resources (GRES) | 180 | COVERED(p3-0610-gres-two-files, m6-10-1)
- ### AutoDetect | 250 | COVERED(p3-0610-autodetect-values)
- ### Manual definition | 240 | COVERED(p3-0610-gres-manual-anatomy)
- ## 2. Requesting GPUs | 310 | COVERED(p3-0610-per-node-vs-total)
- ### Portable resource allocation rules (*Distributed AI Systems* Chapter 8) | 190 | COVERED(p3-0610-portable-header)
- ### What the job sees | 195 | COVERED(h10-task-remap)
- ## 3. Binding GPUs to tasks and CPUs | 365 | COVERED(p3-0610-bind-two-questions, h10-numa-binding)
- ## 4. Isolation: what actually stops a job from using other GPUs | 275 | COVERED(p3-0610-isolation-layers)
- ## 5. Sharing a GPU: MIG, MPS and sharding | 80 | COVERED(p3-0610-sharing-decision, h10-sharing-spectrum)
- ### MIG (Multi-Instance GPU) | 240 | NO FIGURE NEEDED static nature and tradeoffs covered by Section 5 sharing figures
- ### MPS (Multi-Process Service) | 130 | NO FIGURE NEEDED mechanism covered by sharing decision table and spectrum
- ### Sharding | 80 | NO FIGURE NEEDED concise definition covered by sharing decision table
- ### Choosing | 130 | NO FIGURE NEEDED decision table provided in text
- ## 6. Accounting and limits for GPUs | 230 | COVERED(p3-0610-gpu-accounting-levers)
- ## 7. Operational notes | 245 | NO FIGURE NEEDED operational procedures and recommendations
- ### Live GPU job monitoring and distributed profiling (*Distributed AI Systems* Chapter 8) | 360 | NEEDS FIGURE triage flowchart contrasting stragglers, memory exhaustion, and false 100 percent utilization from NCCL spin loops
- ## 8. Troubleshooting | 215 | COVERED(p3-0610-troubleshoot-table)
- ## 9. Lab (self-checking simulator tested; live GPU cluster parts untested) | 280 | NO FIGURE NEEDED lab walkthrough steps
- ## 10. Interview angles | 120 | NO FIGURE NEEDED interview questions
- ## Exercises | 440 | NO FIGURE NEEDED practice problems
- ## Checkpoint | 1000 | NO FIGURE NEEDED review questions and answers
- ## Sources and review notes | 180 | NO FIGURE NEEDED bibliography and verification notes

Specs kept 1, dropped 0: []
