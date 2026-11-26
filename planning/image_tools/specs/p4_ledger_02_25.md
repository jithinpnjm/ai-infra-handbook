# docs/part-02-networking/25-linux-networking-namespaces-veth-bridges-and-container-networking.md
- ## Why this matters for AI infrastructure | 260 | NO FIGURE NEEDED introductory motivation for networking primitives in AI clusters
- ## Prerequisites and outcomes | 90 | NO FIGURE NEEDED prerequisite checklist and chapter mapping
- ## 1. Network namespaces | 240 | COVERED(p3-0225-find-netns, n25-netns)
- ### Interfaces across namespaces | 230 | COVERED(p3-0225-connectors)
- ## 2. Building container networking by hand | 520 | COVERED(p3-0225-container-paths, n25-fig1-veth.jpg, m2-25-1)
- ## 3. Docker networking | 460 | COVERED(p3-0225-docker-nat-bypass, n25-dockermodes)
- ## 4. CNI: the Container Network Interface | 100 | NO FIGURE NEEDED brief conceptual intro to CNI plugin binary model
- ### How it works | 370 | COVERED(p3-0225-cni-contract, n25-cniadd)
- ### Kubernetes network model (requirements) | 90 | COVERED(p3-0225-cni-pick)
- ### Common CNI implementations | 230 | COVERED(p3-0225-cni-pick)
- ## 5. Kubernetes pod networking walkthrough | 30 | NO FIGURE NEEDED short transition text introducing the four walkthrough cases
- ### Same node, bridge-based CNI (e.g. bridge/Flannel host-gw) | 110 | COVERED(p3-0225-calico-routed)
- ### Different nodes | 200 | COVERED(n25-crossnode)
- ### Pod to service and to the outside | 100 | COVERED(p2-0225-clusterip-dnat)
- ### Host networking, pause containers, DNS | 130 | COVERED(p3-0225-hostnet-tradeoff)
- ## 6. Networking for GPU and HPC pods | 640 | COVERED(p3-0225-numa-align, p3-0225-gpu-pod-points, p3-0225-gpu-rails)
- ## 7. Debugging container networking | 360 | COVERED(p3-0225-veth-peer, p2-0225-pod-debug-ladder)
- ## 8. Hands-on lab: build container networking and a mini-CNI | 360 | NO FIGURE NEEDED step-by-step hands-on terminal instructions
- ## 9. Common mistakes | 180 | NO FIGURE NEEDED pure checklist of failure modes and pitfalls
- ## 10. Interview angles | 130 | NO FIGURE NEEDED bulleted list of interview practice prompts
- ## Exercises | 260 | NO FIGURE NEEDED assignment exercises
- ## Checkpoint questions (20) | 1400 | NO FIGURE NEEDED self-test questions and detailed answers
- ## Sources and review notes | 250 | NO FIGURE NEEDED reference list and review metadata

Specs kept 0, dropped 0: []
