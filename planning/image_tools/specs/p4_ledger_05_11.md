# docs/part-05-kubernetes/11-dns-and-service-discovery-with-coredns.md
- ## Why this matters for AI infrastructure | 150 words | NO FIGURE NEEDED - introductory motivation and context
- ## Prerequisites and outcomes | 150 words | NO FIGURE NEEDED - chapter prerequisite checklist
- ## 1. Records Kubernetes creates | 350 words | COVERED(p3-0511-records-by-object)
- ### Reading a Service name | 250 words | COVERED(p2-0511-service-name-parts)
- ## 2. Resolver behaviour inside pods | 250 words | COVERED(p3-0511-dnspolicy-modes)
- ### The ndots:5 problem | 400 words | COVERED(k11-ndots-walk)
- ## 3. CoreDNS architecture | 300 words | COVERED(p3-0511-loop-detected, p3-0511-corefile-annotated, m5-11-1)
- ### Customisation recipes | 250 words | NO FIGURE NEEDED - custom recipes are already visualised in p3-0511-corefile-annotated and code snippets
- ## 4. Scaling and hardening | 50 words | NO FIGURE NEEDED - brief section introduction
- ### Capacity | 350 words | NEEDS FIGURE - beginners struggle to see how proactive cluster-proportional scaling differs from reactive HPA lag during sudden bursts of thousands of pods
- ### NodeLocal DNSCache | 350 words | COVERED(p3-0511-nodelocal-cache)
- ### The conntrack/UDP race and 5-second delays | 250 words | COVERED(k11-conntrack-race)
- ### Other hardening and operations | 300 words | NEEDS FIGURE - beginners struggle to understand the UDP truncation TC bit fallback to TCP 53 and why default-deny NetworkPolicies must allow both protocols
- ## 5. DNS-based discovery for distributed AI workloads | 550 words | COVERED(p3-0511-negative-cache-startup, k11-rendezvous-deadlock)
- ## 6. Observability | 250 words | NO FIGURE NEEDED - clear metric listings, thresholds, and commands
- ## 7. Debugging method | 450 words | COVERED(p3-0511-dns-debug-ladder)
- ## 8. Lab | 450 words | NO FIGURE NEEDED - step-by-step hands-on exercises
- ## 9. Common mistakes | 250 words | NO FIGURE NEEDED - troubleshooting summary checklist
- ## 10. Interview angles | 150 words | NO FIGURE NEEDED - list of interview prompts
- ## Exercises | 350 words | NO FIGURE NEEDED - practice exercises
- ## Checkpoint questions (20) | 1800 words | NO FIGURE NEEDED - self-check Q&A section
- ## Sources and review notes | 250 words | NO FIGURE NEEDED - source bibliography and verification log

Specs kept 2, dropped 0: []
