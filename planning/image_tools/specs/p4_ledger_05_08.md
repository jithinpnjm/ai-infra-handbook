# docs/part-05-kubernetes/08-the-life-of-a-pod-end-to-end-including-what-the-kernel-does.md
- ## Why this matters for AI infrastructure | 250 | NO FIGURE NEEDED introductory motivation and high-level framing
- ## Prerequisites and outcomes | 160 | NO FIGURE NEEDED bulleted checklist of skills and prerequisites
- ## 1. Timeline overview | 300 | COVERED(p2-0508-warm-cold, m5-08-1)
- ## 2. Admission and scheduling (control plane) | 360 | NEEDS FIGURE multi-step request pipeline from kubectl apply through admission mutations, quota validation, etcd commit, and scheduler filter/score/bind phases
- ## 3. The kubelet takes over | 100 | NO FIGURE NEEDED introductory bridge to sync loop covered by subsections
- ### The sync loop | 450 | COVERED(p3-0508-csi-two-step, p3-0508-syncpod-steps, p3-0508-schedule-vs-admit)
- ## 4. Sandbox creation and networking | 260 | COVERED(p3-0508-cni-add-call, k08-sandbox-network)
- ### How CNI `ADD`, IPAM, `readinessGates`, and `podCIDRs` Work (*Networking and Kubernetes* Chapters 3–4 and *Production Kubernetes* Chapter 5) | 500 | COVERED(p3-0508-readiness-gates, p3-0508-veth-finder, p3-0508-pod-cidr)
- ## 5. Images and containers | 450 | COVERED(p3-0508-inspect-kernel-artefacts, p3-0508-container-start-chain, p3-0508-image-pull-queue, k08-namespace-map)
- ### GPU specifics | 250 | COVERED(k08-gpu-isolation)
- ## 6. Running state | 480 | COVERED(p3-0508-oom-vs-eviction)
- ## 7. Termination | 500 | COVERED(p3-0508-who-pulled-trigger, p3-0508-terminating-dominoes, p3-0508-pid1-sigterm, p2-0508-termination-steps)
- ## 8. Measuring pod startup latency | 350 | COVERED(p3-0508-cold-start-fixes, p3-0508-startup-timeline-sources)
- ## 9. Debugging by lifecycle stage | 200 | COVERED(p3-0508-pod-stage-symptoms)
- ## 10. Lab | 350 | NO FIGURE NEEDED step-by-step hands-on terminal exercises
- ## 11. Common mistakes | 250 | NO FIGURE NEEDED prose review of common operational pitfalls
- ## 12. Interview angles | 120 | NO FIGURE NEEDED sample interview question list
- ## Exercises | 220 | NO FIGURE NEEDED practice problem prompts
- ## Checkpoint questions (20) | 1700 | NO FIGURE NEEDED standard self-check Q and A accordion items
- ## Sources and review notes | 300 | NO FIGURE NEEDED citations and bibliography

Specs kept 1, dropped 0: []
