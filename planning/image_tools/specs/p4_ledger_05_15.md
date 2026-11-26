# docs/part-05-kubernetes/15-networkpolicy-and-the-kernel-netfilter-conntrack-and-ebpf.md
- ## Why this matters for AI infrastructure | 170 | NO FIGURE NEEDED introductory motivation using open-plan office metaphor
- ## Prerequisites and outcomes | 210 | NO FIGURE NEEDED prerequisite list and learning checklist
- ## 1. The NetworkPolicy API | 450 | COVERED(p3-0515-gateway-walkthrough, p3-0515-isolation-union)
- ### Selector semantics (a common source of mistakes) | 310 | COVERED(k15-selector-and-or)
- ### Default-deny and baseline patterns | 380 | COVERED(p3-0515-rollout-staging, p2-0515-default-deny-base)
- ### Proving a default deny with a test Pod | 460 | COVERED(k15-deny-proof)
- ## 2. Things NetworkPolicy does not do (and traps) | 500 | COVERED(p3-0515-uncovered-paths)
- ## 3. How enforcement works in the kernel | 160 | COVERED(m5-15-1)
- ### Netfilter basics and conntrack | 220 | COVERED(p2-0515-netfilter-hooks)
- ### Calico (iptables dataplane) | 200 | COVERED(p3-0515-calico-ipset-chains)
- ### Cilium (eBPF) | 230 | COVERED(p2-0515-cilium-identity)
- ### nftables-based and other implementations | 90 | NO FIGURE NEEDED brief prose list of alternative CNI backends
- ### Performance considerations | 190 | NO FIGURE NEEDED prose explanation of O(1) versus O(N) complexity and compile churn
- ## 4. Extended policy models | 50 | NO FIGURE NEEDED introductory transition paragraph
- ### Calico | 160 | NO FIGURE NEEDED short explanation of GlobalNetworkPolicy and order evaluation
- ### Cilium | 200 | NEEDS FIGURE multi-step DNS proxy snooping mechanism required for toFQDNs egress enforcement
- ### Admin and baseline network policies | 160 | COVERED(p2-0515-admin-bookends)
- ### Network identity with Calico and Cilium | 600 | NEEDS FIGURE architectural comparison of Calico Dikastes sidecar versus Cilium eBPF security identity
- ## 5. Policy design for a multi-tenant GPU platform | 580 | COVERED(p2-0515-zone-stance)
- ## 6. Testing and debugging | 460 | COVERED(p2-0515-predict-test)
- ## 7. Lab | 380 | NO FIGURE NEEDED interactive hands-on lab exercises and verification scripts
- ## 8. Common mistakes | 220 | NO FIGURE NEEDED bulleted pitfall summary
- ## 9. Interview angles | 140 | NO FIGURE NEEDED list of interview preparation prompts
- ## Exercises | 240 | NO FIGURE NEEDED end-of-chapter student exercises
- ## Checkpoint questions (20) | 1800 | NO FIGURE NEEDED self-test Q and A review
- ## Sources and review notes | 260 | NO FIGURE NEEDED bibliography and chapter citations

Specs kept 2, dropped 0: []
