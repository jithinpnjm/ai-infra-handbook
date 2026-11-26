# docs/part-06-hpc-slurm/12-multi-node-training-on-slurm-pmix-torchrun-nccl-environment-binding-to.md
- ## Why this matters for AI infrastructure | 160 | NO FIGURE NEEDED introductory narrative on launch failures and motivation
- ## Prerequisites and outcomes | 160 | NO FIGURE NEEDED roadmap of control plane vs data plane and prerequisites
- ## 1. Layers | 170 | COVERED(m6-12-1) stack diagram covers scheduler to fabric layers
- ## 2. Two launch styles | 310 | COVERED(h12-launch-styles) comparison diagram contrasts srun per GPU with torchrun per node
- ## 3. The glue, tested | 470 | COVERED(h12-glue-translation) mapping diagram covers Slurm to PyTorch variable translation
- ## 4. Rendezvous gotchas | 180 | COVERED(p3-0612-rendezvous-checks) checklist diagram covers rendezvous failure modes
- ## 5. NCCL environment variables | 470 | COVERED(p3-0612-nccl-info-baseline, p3-0612-nccl-vars-groups) baseline log comparison and variable groupings cover NCCL configuration
- ## 6. Binding for training jobs | 350 | NEEDS FIGURE layout of 8-GPU HGX rail-optimized NUMA domains, GPUs, NICs, and cross-socket penalty
- ## 7. Framework patterns | 640 | COVERED(p3-0612-megatron-ckpt-math, p3-0612-framework-exports, h12-master-addr-trap) checkpoint size bars, framework comparison table, and loopback trap covered
- ## 8. Failure and diagnosis | 360 | COVERED(p3-0612-hang-symptoms, h12-diagnose-ladder) symptoms table and 3-step diagnostic ladder covered
- ### 8.1 When the job hangs: flight recorder and ncclras | 160 | COVERED(p3-0612-flight-recorder-ras) flight recorder ring buffer vs ncclras comparison covered
- ### 8.2 Six multinode communication pitfalls | 240 | COVERED(p3-0612-six-comm-pitfalls) cards cover 6 multinode communication pitfalls
- ### 8.3 Six NCCL communicator and environment gotchas | 230 | COVERED(p3-0612-six-nccl-gotchas) cards cover 6 communicator lifecycle gotchas
- ## 9. Lab | 250 | NO FIGURE NEEDED step-by-step lab instructions
- ## 10. Interview angles | 90 | NO FIGURE NEEDED bulleted interview prompts
- ## Exercises | 310 | NO FIGURE NEEDED exercise prompts and calculation instructions
- ## Checkpoint | 1100 | NO FIGURE NEEDED review questions and collapsible answers
- ## Sources and review notes | 470 | NO FIGURE NEEDED bibliography and verification notes

Specs kept 1, dropped 0: []
