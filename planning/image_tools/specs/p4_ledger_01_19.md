# docs/part-01-linux/19-namespaces-the-kernel-feature-behind-containers.md
- ## Why this matters for AI infrastructure | 250 | NO FIGURE NEEDED introductory motivation and failure list
- ## Prerequisites and outcomes | 180 | NO FIGURE NEEDED prerequisite checklist and learning outcomes
- ## 1. A container is not a kernel object | 320 | COVERED(ch19-d1-luna)
- ## 2. The namespace types | 350 | COVERED(l19-ns-syscalls)
- ### Inspecting namespaces | 170 | COVERED(p3-0119-nsenter-recipe)
- ## 3. PID namespaces | 340 | COVERED(p3-0119-pid1-sigterm)
- ### Seeing a container from the host | 120 | COVERED(ch19-d2-luna)
- ## 4. Mount namespaces, root changes and OverlayFS | 20 | NO FIGURE NEEDED structural section header
- ### Mount namespaces and propagation | 230 | COVERED(l19-mount-propagation)
- ### chroot versus pivot_root | 190 | COVERED(l19-chroot-pivot)
- ### OverlayFS: images as layers | 480 | COVERED(p3-0119-overlay-writes-land)
- ### Reading an overlay mount on the host | 210 | COVERED(p3-0119-dockerfile-layers)
- ## 5. Network namespaces | 380 | COVERED(p3-0119-net-modes)
- ## 6. User namespaces, UID mapping and rootless containers | 320 | COVERED(ch19-d6-luna)
- ## 7. UTS, IPC, cgroup and time namespaces | 240 | COVERED(p3-0119-shm-bus-error)
- ## 8. Putting it together: what a runtime does | 150 | COVERED(p3-0119-pod-namespace-knobs)
- ## 9. Containers, VMs and lightweight VMs | 220 | COVERED(l19-isolation-compare)
- ## 10. Observing containers (and the traps) | 280 | COVERED(p3-0119-observe-traps)
- ## 11. GPUs inside containers | 260 | COVERED(p3-0119-gpu-three-steps)
- ## 12. Other flavours of "virtual" | 320 | NEEDS FIGURE 4-way comparison across language envs, HPC unprivileged containers, app containers, and system containers
- ## 13. Failure modes and diagnosis | 240 | COVERED(p3-0119-five-questions)
- ## 14. Hands-on lab: explore and build with namespaces | 460 | NO FIGURE NEEDED step-by-step terminal lab walkthrough
- ## 15. Common mistakes | 170 | NO FIGURE NEEDED bulleted checklist of common operational traps
- ## 16. Interview angles | 120 | NO FIGURE NEEDED interview question list
- ## Exercises | 290 | NO FIGURE NEEDED practice homework problems
- ## Checkpoint questions (20) | 1200 | NO FIGURE NEEDED question and answer self-test block
- ## Sources and review notes | 240 | NO FIGURE NEEDED citations and provenance metadata

Specs kept 1, dropped 0: []
